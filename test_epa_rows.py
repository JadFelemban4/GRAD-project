"""test_epa_rows.py -- the leak-proof loader's self-test: each guard shown able to fail, the
poison proof, the masks, the scans and the runtime audit.

    python test_epa_rows.py     about a minute; exit code 0 when all pass

Build step 2 of decision 24, WP3 (23 October 2026; docs/build_step_2/PLAN.md section 4.6 as
amendments C2-C5, C8 and C9 of docs/build_step_2/AMENDMENTS.md correct it; HANDOFFS.md WP3 item
6; WP3_INTERFACES.md section 9.3). Every proof comes with a control that must fail (mistake 12).

  Synthetic   temporary git repositories with synthetic tables and contract (test_epa_fixtures):
              the counts and the partition (yielded and H disjoint, together every id, every
              yielded line outside L); each corruption stops the loader and passes with its
              guard switched off -- a held id deleted, a held id shifted by one, a line removed
              from L with its rows kept (in H, and out of it), one byte of a table changed, the
              root's split.py and the imported one changed, a contract differing from its commit,
              a contract commit that is not an ancestor, another schema, a calibration id at a
              held line's speed, a held row parsed, a header changed, the ids out of order, an
              Initial and a Final row on two lines, a required cell empty; a speed in no line;
              the masks (an Initial row has no TIT, lambda or MAP; no ALPHA curve and no
              held-out key reachable); the poison three ways (C8): the yield, the view and the
              manifest byte-identical, and a parsed held row would meet the poison; the
              garbled-key contract gives the same view and yield (C4), a garbled read key is
              caught; decision 54's flags (a -120 spark, an empty spark, an empty lambda, an
              empty HD1 bank, an empty meter) and their controls; the table fuel's LHV from the
              decimal string (WP3_INTERFACES 5.1), against a decimal whose product by 1e6 differs
  Audit       the loader, run in a subprocess of a synthetic repository under an audit hook,
              opens only its own engine's tables, epa_engine.json, the contract, the K3 file
              and code; an extra open of epa_channels.csv is flagged (the control)
  Structural  the real tables, the only class that opens them: the guards pass; the counts are
              the contract's; yielded and H disjoint by keys; calibration_coverage equals the
              contract's coverage.calibration_* exactly (C9); split.compute() hashes to
              generator_inputs_sha256["split.json"] (plan 4.6 item 2); the yield and the manifest
              unchanged when every held-out cell of scratch copies is poisoned, three ways; the
              contract's rounded lambda_ref and hot floor move no calibration population. It
              prints booleans and counts only, never a value
  CarriedPins test_carried.py's pins (OWN_ENGINE, LINE_ENDS, the fuels, lam_floor) against
              calibration_contract and engine_facts' non-curve fields (HANDOFFS WP3 item 6); the
              Mazda's table fuels equal its typed fuel to the bit. It reads the real contract and
              epa_engine.json, never a table
  Scans       every rule of WP3_INTERFACES 3.1 and 3.2 over every step-2 module and test that
              exists, and N9 over every .py git would commit; each rule run once on a scratch
              source that breaks it, which must be flagged; the patterns built from parts
  Columns     every pinned header column is in exactly one of FIELD_OF_COLUMN and
              DROPPED_COLUMNS; the pins of epa_map.py's KEY_COLUMNS, PROVENANCE, FIRST_DATA_ROW
              and channel names equal its literals (read as source, never imported)
"""
import ast
import contextlib
import csv
import dataclasses
import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import epa_rows as R  # noqa: E402
import test_epa_fixtures as F  # noqa: E402
from thresholds import common, split  # noqa: E402

ENGINES = tuple(R.TABLES)
MZ = "mazda_25t"                         # the engine most corruption tests use, named at every call
STOP = (R.LoaderStop, KeyError)          # what a corrupted load raises


def off(*names):
    """Switch the named guards of epa_rows off (each becomes a no-op) for the block."""
    stack = contextlib.ExitStack()
    for n in names:
        if not hasattr(R, n):
            raise AttributeError(n)
        stack.enter_context(mock.patch.object(R, n, lambda *a, **k: None))
    return stack


def keys_of(rows):
    return {(r.table, r.source_row) for r in rows}


# ============================================================================ Synthetic
class Synthetic(F.SyntheticRepoCase):
    """Temporary repositories only (amendment C5)."""

    def src(self, repo, **kw):
        return dataclasses.replace(F.synthetic_source(repo), **kw)

    # ---------------------------------------------------------------- counts and partition
    def test_counts_and_partition(self):
        src = F.synthetic_source(self.base)
        c = F.read_contract(self.base)
        for eng in ENGINES:
            y = R.calibration_rows(eng, source=src)
            view = R.calibration_contract(eng, source=src)
            H = R.held_out_keys(eng, source=src)
            held = {(t, s) for t, rows in H.items() for s in rows}
            self.assertEqual(keys_of(y.rows) & held, set(), eng)
            for t in y.counts:
                ids = {(t.name, s) for s in range(R.FIRST_DATA_ROW, R.FIRST_DATA_ROW + t.rows)}
                mine = {k for k in keys_of(y.rows) if k[0] == t.name} | {k for k in held if k[0] == t.name}
                self.assertEqual(mine, ids, t.name)
            self.assertEqual(y.counts, view.table_counts)
            self.assertFalse({r.line for r in y.rows} & set(view.held_out_lines), eng)
            self.assertTrue({rec["line"] for rec in c["engines"][eng]["held_out_rows"]} <= set(view.held_out_lines))
            self.assertGreater(len(held), 0)
            # the types: steady, Final and Initial rows, never a held-out type
            self.assertEqual({type(r) for r in y.rows}, {R.SteadyRow, R.FinalRow, R.InitialRow})

    def test_a_second_load_is_byte_identical(self):
        src = F.synthetic_source(self.base)
        a, b = R.calibration_rows("ford_27tt", source=src), R.calibration_rows("ford_27tt", source=src)
        self.assertEqual(a.sha256, b.sha256)
        self.assertEqual(a.manifest.sha256, R.manifest("ford_27tt", source=src).sha256)

    # ---------------------------------------------------------------- corruptions
    def stops(self, repo, guards, *, engine, source, exc):
        """The loader stops on repo (on `source` when it is not None); with `guards` switched off
        it loads. Returns the yield. Every argument explicit (mistake 1: no default engine)."""
        src = source or F.synthetic_source(repo)
        with self.assertRaises(exc):
            R.calibration_rows(engine, source=src)
        with off(*guards):
            return R.calibration_rows(engine, source=src)

    def a_held_row(self, repo, *, engine, role):
        spec = next(s for s in R.TABLES[engine] if s.role == role)
        rows = F.held_rows(repo, engine)[spec.name]
        return spec, rows

    def test_a_held_id_deleted(self):
        repo = self.fresh()
        spec, rows = self.a_held_row(repo, engine=MZ, role="steady")
        gone = rows[0]
        repo = F.rewrite_contract(repo, lambda c: c["engines"]["mazda_25t"].__setitem__(
            "held_out_rows", [r for r in c["engines"]["mazda_25t"]["held_out_rows"]
                              if (r["table"], r["source_row"]) != (spec.name, gone)]))
        y = self.stops(repo, ("_guard_line", "_guard_counts"), source=None, exc=STOP, engine=MZ)
        self.assertIn((spec.name, gone), keys_of(y.rows))            # the leak the guards stop

    def test_a_held_id_shifted_by_one(self):
        repo = self.fresh()
        spec, rows = self.a_held_row(repo, engine=MZ, role="steady")
        last = min(r for r in rows if r + 1 not in rows)               # the next row is a calibration row

        def edit(c):
            for r in c["engines"]["mazda_25t"]["held_out_rows"]:
                if (r["table"], r["source_row"]) == (spec.name, last):
                    r["source_row"] = last + 1
        repo = F.rewrite_contract(repo, edit)
        y = self.stops(repo, ("_guard_line",), source=None, exc=STOP, engine=MZ)
        self.assertIn((spec.name, last), keys_of(y.rows))

    def test_a_line_removed_from_L_with_its_rows_kept_in_H(self):
        repo = self.fresh()
        line = F.read_contract(repo)["engines"]["mazda_25t"]["held_out_lines"][0]
        repo = F.rewrite_contract(repo, lambda c: c["engines"]["mazda_25t"]["held_out_lines"].remove(line))
        self.stops(repo, ("_guard_held_structure",), source=None, exc=STOP, engine=MZ)

    def test_a_line_removed_from_L_and_H_with_its_rows_kept_in_the_tables(self):
        repo = self.fresh()
        line = F.read_contract(repo)["engines"]["mazda_25t"]["held_out_lines"][0]

        def edit(c):
            e = c["engines"]["mazda_25t"]
            e["held_out_lines"].remove(line)
            e["held_out_rows"] = [r for r in e["held_out_rows"] if r["line"] != line]
        repo = F.rewrite_contract(repo, edit)
        y = self.stops(repo, ("_guard_counts",), source=None, exc=STOP, engine=MZ)
        self.assertIn(line, {r.line for r in y.rows})

    def test_one_byte_of_a_table_changed(self):
        repo = self.fresh()
        _, held = self.a_held_row(repo, engine=MZ, role="steady")

        def edit(header, rows):
            i_sr, i_t = header.index("source_row"), header.index("turbine_inlet_temp_c")
            r = next(r for r in rows if int(r[i_sr]) not in held)
            r[i_t] = r[i_t][:-1] + ("7" if r[i_t][-1] != "7" else "8")         # its last digit
            return rows
        path = F.table_file(repo.root, "mazda_25t", "steady", 0)
        with open(path, "rb") as fh:
            before = fh.read()
        F.edit_table(path, edit)
        with open(path, "rb") as fh:
            after = fh.read()
        self.assertEqual((len(after), sum(a != b for a, b in zip(before, after))), (len(before), 1))
        y = self.stops(repo, ("_guard_table_hash",), exc=R.LoaderStop, source=None, engine=MZ)
        self.assertNotEqual(y.sha256, R.calibration_rows("mazda_25t", source=F.synthetic_source(self.base)).sha256)

    def test_a_different_split_py_in_the_root(self):
        repo = self.fresh()
        with open(os.path.join(repo.root, "thresholds", "split.py"), "ab") as fh:
            fh.write(b"# one more line\n")
        self.stops(repo, ("_guard_generators",), exc=R.LoaderStop, source=None, engine=MZ)

    def test_a_different_split_py_imported(self):
        tmp = tempfile.mkdtemp(dir=self._tmp.name)
        changed = os.path.join(tmp, "split.py")
        shutil.copyfile(split.__file__, changed)
        with open(changed, "ab") as fh:
            fh.write(b"# one more line\n")
        files = {"thresholds/split.py": changed, "thresholds/common.py": common.__file__}
        with mock.patch.object(R, "_imported_generator_files", lambda: files):
            self.stops(self.base, ("_guard_generators",), exc=R.LoaderStop, source=None, engine=MZ)

    def test_a_contract_differing_from_its_commit(self):
        for which in (0, 1):                                          # the JSON, then the MD
            repo = self.fresh()
            path = F._contract_paths(repo.root)[which]
            with open(path, "ab") as fh:
                fh.write(b" ")
            self.stops(repo, ("_guard_contract_blob",), exc=R.LoaderStop, source=None, engine=MZ)

    def test_a_contract_commit_that_is_not_an_ancestor(self):
        repo = self.fresh()
        F.git(repo.root, "checkout", "-q", "-b", "side")
        side = F.commit_all(repo.root, "a side commit")
        F.git(repo.root, "checkout", "-q", "main")
        self.stops(repo, ("_guard_contract_ancestor",), source=self.src(repo, contract_commit=side),
                   exc=R.LoaderStop, engine=MZ)

    def test_another_schema(self):
        repo = F.rewrite_contract(self.fresh(), lambda c: c.__setitem__("schema", 3))
        self.stops(repo, ("_guard_schema",), exc=R.LoaderStop, source=None, engine=MZ)

    def test_a_calibration_id_at_a_held_lines_speed(self):
        repo = self.fresh()
        held_line = F.read_contract(repo)["engines"]["mazda_25t"]["held_out_lines"][0]
        spec, held = self.a_held_row(repo, engine=MZ, role="steady")
        moved = []

        def edit(header, rows):
            i_sr, i_s = header.index("source_row"), header.index("speed_rpm")
            for r in rows:
                if int(r[i_sr]) not in held and not moved:
                    r[i_s] = repr(float(held_line) + 2.0)
                    moved.append(int(r[i_sr]))
            return rows
        F.edit_table(F.table_file(repo.root, "mazda_25t", "steady", 0), edit)
        repo = F.rehash_tables(repo)
        with self.assertRaises(R.SplitViolation):
            R.calibration_rows("mazda_25t", source=F.synthetic_source(repo))
        with off("_guard_line"):
            y = R.calibration_rows("mazda_25t", source=F.synthetic_source(repo))
        self.assertIn(held_line, {r.line for r in y.rows})

    def test_a_held_row_parsed(self):
        src = F.synthetic_source(self.base)
        spec, held = self.a_held_row(self.base, engine=MZ, role="steady")
        leak = held[0]
        real = R._is_held

        def broken(table, sr, h):
            return False if (table, sr) == (spec.name, leak) else real(table, sr, h)
        with mock.patch.object(R, "_is_held", broken):
            with self.assertRaises(R.SplitViolation):
                R.calibration_rows("mazda_25t", source=src)
            with off("_guard_line", "_guard_held_seen", "_guard_counts"):
                y = R.calibration_rows("mazda_25t", source=src)
        self.assertIn((spec.name, leak), keys_of(y.rows))

    def test_a_header_changed(self):
        repo = self.fresh()
        path = F.table_file(repo.root, "mazda_25t", "final", 0)
        with open(path, "rb") as fh:
            data = fh.read().replace(b"turbine_inlet_temp_c", b"turbine_inlet_temp_k", 1)
        with open(path, "wb") as fh:
            fh.write(data)
        repo = F.rehash_tables(repo)
        self.stops(repo, ("_guard_header",), exc=R.LoaderStop, source=None, engine=MZ)

    def test_the_ids_out_of_order(self):
        repo = self.fresh()
        _, held = self.a_held_row(repo, engine=MZ, role="steady")

        def edit(header, rows):
            i_sr = header.index("source_row")
            cal = [k for k, r in enumerate(rows) if int(r[i_sr]) not in held]
            a, b = cal[0], cal[1]
            rows[a], rows[b] = rows[b], rows[a]
            return rows
        F.edit_table(F.table_file(repo.root, "mazda_25t", "steady", 0), edit)
        repo = F.rehash_tables(repo)
        self.stops(repo, ("_guard_ids",), exc=R.LoaderStop, source=None, engine=MZ)

    def test_an_initial_and_its_final_row_on_two_lines(self):
        repo = self.fresh()
        _, held = self.a_held_row(repo, engine=MZ, role="initial")
        c = F.read_contract(repo)["engines"]["mazda_25t"]
        cal_lines = [ln for ln in c["lines"] if ln not in c["held_out_lines"]]

        def edit(header, rows):
            i_sr, i_s = header.index("source_row"), header.index("speed_rpm")
            for r in rows:
                if int(r[i_sr]) not in held:
                    here = str(int(round(float(r[i_s]) / 50.0) * 50))
                    other = next(ln for ln in cal_lines if ln != here)
                    r[i_s] = repr(float(other) + 1.0)
                    break
            return rows
        F.edit_table(F.table_file(repo.root, "mazda_25t", "initial", 0), edit)
        repo = F.rehash_tables(repo)
        self.stops(repo, ("_guard_pairs",), exc=R.LoaderStop, source=None, engine=MZ)

    def test_a_required_cell_empty(self):
        repo = self.fresh()
        _, held = self.a_held_row(repo, engine=MZ, role="steady")

        def edit(header, rows):
            i_sr, i_t = header.index("source_row"), header.index("torque_nm")
            next(r for r in rows if int(r[i_sr]) not in held)[i_t] = ""
            return rows
        F.edit_table(F.table_file(repo.root, "mazda_25t", "steady", 0), edit)
        repo = F.rehash_tables(repo)
        y = self.stops(repo, ("_guard_finite",), exc=R.LoaderStop, source=None, engine=MZ)
        self.assertIn(None, {r.torque_nm for r in y.rows if isinstance(r, R.SteadyRow)})

    def test_a_speed_in_no_line_raises_key_error(self):
        repo = self.fresh()
        _, held = self.a_held_row(repo, engine=MZ, role="steady")

        def edit(header, rows):
            i_sr, i_s = header.index("source_row"), header.index("speed_rpm")
            next(r for r in rows if int(r[i_sr]) not in held)[i_s] = "9001.0"
            return rows
        F.edit_table(F.table_file(repo.root, "mazda_25t", "steady", 0), edit)
        repo = F.rehash_tables(repo)
        with self.assertRaises(KeyError):
            R.calibration_rows("mazda_25t", source=F.synthetic_source(repo))
        R.calibration_rows("mazda_25t", source=F.synthetic_source(self.base))        # the control

    def test_the_contract_must_be_the_roots_own(self):
        repo = self.fresh()
        tmp = tempfile.mkdtemp(dir=self._tmp.name)
        copy_json = os.path.join(tmp, "contract.json")
        shutil.copyfile(F.synthetic_source(repo).contract_json, copy_json)
        with self.assertRaises(R.LoaderStop):
            R.calibration_rows("mazda_25t", source=self.src(repo, contract_json=copy_json))
        # the same copy is accepted in a poison run, where it is checked key by key
        R.calibration_contract("mazda_25t", source=self.src(repo, contract_json=copy_json, allow_poisoned_tables=True))

    # ---------------------------------------------------------------- masks
    def test_an_initial_row_has_no_tit_lambda_map_or_fuel(self):
        y = R.calibration_rows("mazda_25t", source=F.synthetic_source(self.base))
        r = next(x for x in y.rows if isinstance(x, R.InitialRow))
        for name in ("tit_c", "turbine_inlet_temp_c", "lam_meas", "map_kpa", "fuel_meter_gps", "injector_fuel_gps"):
            with self.assertRaises(AttributeError):
                getattr(r, name)
        self.assertTrue(r.transient)
        f = next(x for x in y.rows if isinstance(x, R.FinalRow))           # the control
        self.assertEqual(f.hold, r.hold if f.source_row == r.source_row else f.source_row)
        self.assertTrue(math.isfinite(f.tit_c))

    def test_no_alpha_curve_and_no_held_out_key_is_reachable(self):
        src = F.synthetic_source(self.base)
        for eng in ENGINES:
            facts = R.engine_facts(eng, source=src)
            blob = R.canonical_json(facts).decode()
            for word in ("wot_torque_curve", "closed_throttle_torque_curve", "measured_at_speed", "node_is_measured"):
                self.assertNotIn(word, blob)
            view = R.calibration_contract(eng, source=src).as_json()
            found = set()

            def walk(o):
                if isinstance(o, dict):
                    found.update(o)
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(view)
            forbidden = {"held_out_rows", "per_held_out_line", "deciding_lines", "pooled_counts", "offsets",
                         "eligible", "alpha_nodes_removed", "where", "deepest_epa_lambda_cell_referenced",
                         "fired_steady_and_final", "fired_intake_temp_c", "hot_intake_temp_c"}
            self.assertEqual(found & forbidden, set(), eng)
            # the control: the synthetic contract holds every one of them
            e = F.read_contract(self.base)["engines"][eng]
            found = set()
            walk(e)
            self.assertEqual(forbidden - found, set())

    # ---------------------------------------------------------------- poison (C8) and garbled keys (C4)
    def test_poison_three_ways_moves_nothing(self):
        src = F.synthetic_source(self.base)
        for eng in ENGINES:
            y0, v0 = R.calibration_rows(eng, source=src), R.calibration_contract(eng, source=src)
            for how in R.POISONS:
                dst = tempfile.mkdtemp(dir=self._tmp.name)
                ps = R.poisoned_tables(eng, source=src, dst_dir=dst, how=how)
                self.assertTrue(ps.allow_poisoned_tables)
                # the copies differ from the tables: the poison is there
                for spec in R.TABLES[eng]:
                    self.assertNotEqual(common.sha_raw(R.table_path(spec, source=ps)),
                                        common.sha_raw(R.table_path(spec, source=src)), (eng, how, spec.name))
                y = R.calibration_rows(eng, source=ps)
                self.assertEqual((y.sha256, y.manifest.sha256), (y0.sha256, y0.manifest.sha256), (eng, how))
                self.assertEqual(R.manifest(eng, source=ps).sha256, y0.manifest.sha256)
                self.assertEqual(R.calibration_contract(eng, source=ps).sha256, v0.sha256)
                self.assertEqual(R.calibration_coverage(eng, source=ps), R.calibration_coverage(eng, source=src))
                # epa_engine.json's copy: every key engine_facts never reads garbled (the ALPHA curves hold
                # held-out torques, amendment C7), so its bytes differ and its facts do not (WP3's fix of 23
                # October 2026)
                jp = os.path.join(ps.engine_dir, eng, "epa_engine.json")
                self.assertNotEqual(common.sha_raw(jp), common.sha_raw(os.path.join(src.engine_dir, eng, "epa_engine.json")))
                self.assertEqual(R.engine_facts(eng, source=ps), R.engine_facts(eng, source=src))
        # the control: a key engine_facts reads, changed in a copy, moves the facts
        with open(jp, encoding="utf-8") as fh:
            j = json.load(fh)
        j["alpha_fuel"] = {"research_octane_number": -1.0}
        with open(jp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(j, fh)
        self.assertNotEqual(R.engine_facts(ENGINES[-1], source=ps), R.engine_facts(ENGINES[-1], source=src))

    def test_poison_control_a_calibration_cell_changed_moves_the_yield(self):
        src = F.synthetic_source(self.base)
        y0 = R.calibration_rows("mazda_25t", source=src)
        ps = R.poisoned_tables("mazda_25t", source=src, dst_dir=tempfile.mkdtemp(dir=self._tmp.name), how="high")
        _, held = self.a_held_row(self.base, engine=MZ, role="steady")

        def edit(header, rows):
            i_sr, i_t = header.index("source_row"), header.index("turbine_inlet_temp_c")
            r = next(r for r in rows if int(r[i_sr]) not in held)
            r[i_t] = repr(float(r[i_t]) + 1.0)
            return rows
        F.edit_table(R.table_path(R.TABLES["mazda_25t"][0], source=ps), edit)
        with self.assertRaises(R.LoaderStop):
            R.calibration_rows("mazda_25t", source=ps)
        with off("_guard_poisoned_table"):
            y = R.calibration_rows("mazda_25t", source=ps)
        self.assertNotEqual(y.sha256, y0.sha256)
        self.assertNotEqual(y.manifest.sha256, y0.manifest.sha256)

    def test_poison_control_a_parsed_held_row_meets_the_poison(self):
        """If a held row were parsed, the low poison's speed (-1e6 rpm) has no line: the loader
        stops with KeyError, so the poison reaches whatever reads a held cell."""
        src = F.synthetic_source(self.base)
        ps = R.poisoned_tables("mazda_25t", source=src, dst_dir=tempfile.mkdtemp(dir=self._tmp.name), how="low")
        spec, held = self.a_held_row(self.base, engine=MZ, role="steady")
        real = R._is_held
        with mock.patch.object(R, "_is_held", lambda t, s, h: False if (t, s) == (spec.name, held[0]) else real(t, s, h)):
            with self.assertRaises(KeyError):
                R.calibration_rows("mazda_25t", source=ps)

    def test_the_garbled_key_contract_gives_the_same_view_and_yield(self):
        src = F.synthetic_source(self.base)
        dst = os.path.join(tempfile.mkdtemp(dir=self._tmp.name), "garbled.json")
        R.garbled_contract(src.contract_json, dst)
        with open(dst, encoding="utf-8") as fh:
            g = json.load(fh)
        c = F.read_contract(self.base)
        self.assertNotEqual(g["engines"]["mazda_25t"]["per_held_out_line"], c["engines"]["mazda_25t"]["per_held_out_line"])
        self.assertNotEqual(g["engines"]["mazda_25t"]["lambda_clip_floor"]["where"],
                            c["engines"]["mazda_25t"]["lambda_clip_floor"]["where"])
        self.assertEqual(g["engines"]["mazda_25t"]["held_out_rows"], c["engines"]["mazda_25t"]["held_out_rows"])
        gs = dataclasses.replace(src, contract_json=dst, allow_poisoned_tables=True)
        for eng in ENGINES:
            self.assertEqual(R.calibration_contract(eng, source=gs).sha256, R.calibration_contract(eng, source=src).sha256)
            self.assertEqual(R.calibration_rows(eng, source=gs).sha256, R.calibration_rows(eng, source=src).sha256)

    def test_garbled_control_a_read_key_garbled_is_caught(self):
        src = F.synthetic_source(self.base)
        dst = os.path.join(tempfile.mkdtemp(dir=self._tmp.name), "garbled.json")
        c = F.read_contract(self.base)
        name = R.TABLES["mazda_25t"][0].name
        c["engines"]["mazda_25t"]["lambda_ref"][name] = 0.5
        with open(dst, "w", encoding="utf-8") as fh:
            json.dump(c, fh, indent=1)
        gs = dataclasses.replace(src, contract_json=dst, allow_poisoned_tables=True)
        with self.assertRaises(R.LoaderStop):
            R.calibration_contract("mazda_25t", source=gs)
        with off("_guard_poisoned_contract"):
            self.assertNotEqual(R.calibration_contract("mazda_25t", source=gs).sha256,
                                R.calibration_contract("mazda_25t", source=src).sha256)

    # ---------------------------------------------------------------- decision 54's flags
    def row_at(self, y, table_role, line, i, *, engine, index):
        spec = next(s for s in R.TABLES[engine] if (s.role, s.index) == (table_role, index))
        order = F._rows_of(F.DEFAULT_SPECS[engine], spec)
        sr = R.FIRST_DATA_ROW + order.index((line, i))
        return next(r for r in y.rows if (r.table, r.source_row) == (spec.name, sr))

    def test_decision_54s_flags_and_their_controls(self):
        src = F.synthetic_source(self.base)
        y = R.calibration_rows("mazda_25t", source=src)
        s = self.row_at(y, "steady", "3000", 0, engine=MZ, index=0)                           # -120
        self.assertTrue(s.spark_sentinel)
        self.assertIsNone(s.spark_btdc)
        e = self.row_at(y, "steady", "4000", 3, engine=MZ, index=0)                           # an empty spark cell
        self.assertTrue(e.spark_sentinel)
        self.assertIsNone(e.spark_btdc)
        lm = self.row_at(y, "steady", "2500", 2, engine=MZ, index=0)                          # an empty lambda, fired
        self.assertTrue(lm.lambda_missing and lm.pops.fired)
        self.assertIsNone(lm.lam_meas)
        self.assertFalse(lm.pops.hot_l1 or lm.pops.hot_enr or lm.pops.l1_thr or lm.pops.l1_boost)
        m = self.row_at(y, "final", "3000", 1, engine=MZ, index=0)                            # an empty meter on a Final row
        self.assertTrue(m.meter_missing and m.fuel_meter_gps is None and not m.pops.fired_meter)
        ok = self.row_at(y, "steady", "2500", 3, engine=MZ, index=0)                          # the control
        self.assertFalse(ok.spark_sentinel or ok.lambda_missing or ok.meter_missing)
        self.assertIsInstance(ok.spark_btdc, float)
        yf = R.calibration_rows("ford_27tt", source=src)
        hd1 = self.row_at(yf, "steady", "2000", 3, engine="ford_27tt", index=1)   # an empty HD1 bank
        self.assertTrue(hd1.lambda_missing)
        self.assertIsNone(hd1.lam_meas)
        self.assertIsNone(hd1.lam_banks[1])
        self.assertIsInstance(hd1.lam_banks[0], float)
        hd1_ok = self.row_at(yf, "steady", "2000", 2, engine="ford_27tt", index=1)
        self.assertEqual(hd1_ok.lam_meas, 0.5 * (hd1_ok.lam_banks[0] + hd1_ok.lam_banks[1]))
        self.assertIsNone(hd1_ok.baro_kpa)                                  # HD1 publishes no cell pressure
        self.assertIsInstance(hd1_ok.cell_temp_k, float)                    # but a cell temperature
        self.assertIsNone(hd1_ok.cam_cad)
        self.assertTrue(hd1_ok.cam_missing and hd1_ok.cam_channel is None)
        # decision 54's two sentinels told apart (spark_empty, stage0.json's sentinel_value and empty_cell;
        # WP3's integration, 23 October 2026): the -120 is no empty cell, the empty cell is, the control
        # neither
        self.assertEqual((s.spark_empty, e.spark_empty, ok.spark_empty), (False, True, False))

    # ---------------------------------------------------------------- WP3's integration (23 October 2026)
    def test_run1_wait_reads_the_rule_and_nothing_else(self):
        repo = self.fresh()
        self.assertIsNone(R.run1_wait(source=F.synthetic_source(repo)), "no open_for_the_team, no rule")
        rule = "synthetic: The first fit (Run 1) waits for both columns"
        repo2 = F.rewrite_contract(repo, lambda c: c.__setitem__("open_for_the_team", ["other", rule]))
        self.assertEqual(R.run1_wait(source=F.synthetic_source(repo2)), rule)
        # it fails closed (WP3's fix of 23 October 2026): an entry that names Run 1 in other words holds it;
        # the control, an entry that names no Run 1, holds nothing at a commit that is not the pinned one
        repo3 = F.rewrite_contract(repo2, lambda c: c.__setitem__("open_for_the_team", ["Run 1 is described here"]))
        self.assertEqual(R.run1_wait(source=F.synthetic_source(repo3)), "Run 1 is described here")
        repo4 = F.rewrite_contract(repo3, lambda c: c.__setitem__("open_for_the_team", ["the roads come later"]))
        self.assertIsNone(R.run1_wait(source=F.synthetic_source(repo4)))
        with mock.patch.object(R, "CONTRACT_COMMIT", repo4.contract_commit):     # the pinned commit holds it
            self.assertEqual(R.run1_wait(source=F.synthetic_source(repo4)), R.RUN1_PINNED_COMMIT)
        # the rule is read off the verified contract: a contract that is not its commit's stops first
        cj = F.synthetic_source(repo2).contract_json
        with open(cj, "ab") as fh:
            fh.write(b" ")
        with self.assertRaises(R.LoaderStop):
            R.run1_wait(source=F.synthetic_source(repo2))

    def test_audit_paths_name_the_engines_files_from_the_source(self):
        src = F.synthetic_source(self.base)
        p = R.audit_paths(MZ, source=src)
        self.assertEqual(set(p["table_files"]),
                         {os.path.relpath(R.table_path(t, source=src), src.root).replace(os.sep, "/")
                          for t in R.TABLES[MZ]})
        self.assertTrue(p["own"].startswith(p["engines"] + "/"))
        self.assertEqual(len(p["channels"]), len(R.TABLES))
        self.assertTrue(all(c.endswith("epa_channels.csv") for c in p["channels"]))
        for k in ("engine_json", "k3", "outputs", "validation"):
            self.assertFalse(os.path.isabs(p[k]), k)
        self.assertTrue(os.path.isabs(p["data_folder"]))
        with self.assertRaises(ValueError):
            R.audit_paths("b58", source=src)

    def test_the_counts_record_is_the_yields(self):
        y = R.calibration_rows(MZ, source=F.synthetic_source(self.base))
        rec = R.table_counts_record(y)
        self.assertEqual(len(rec), 1)
        block = rec[next(iter(rec))]                       # its one key, the tables' (rule N1 keeps it in epa_rows)
        self.assertEqual({k: (v["rows"], v["calibration"], v["held_out_skipped"]) for k, v in block.items()},
                         {c.name: (c.rows, c.calibration, c.held_out_skipped) for c in y.counts})

    def test_the_units_and_the_populations_are_the_generators(self):
        src = F.synthetic_source(self.base)
        y = R.calibration_rows("honda_l15b7", source=src)
        r = next(x for x in y.rows if isinstance(x, R.SteadyRow))
        spec = next(s for s in R.TABLES["honda_l15b7"] if s.name == r.table)
        with open(R.table_path(spec, source=src), newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        raw = next(x for x in rows if int(x["source_row"]) == r.source_row)
        self.assertEqual(r.imt_k, float(raw["intake_manifold_temp_c"]) + 273.15)
        self.assertEqual(r.tit_c, float(raw["turbine_inlet_temp_c"]))
        self.assertEqual(r.cam_channel, "intake_cam_phase_cad_adv")
        view = R.calibration_contract("honda_l15b7", source=src)
        want = split.classify(raw, view.lambda_ref[r.table], view.hot_map_floor_kpa, "steady")
        self.assertEqual({k: getattr(r.pops, k) for k in R._POP_KEYS}, {k: bool(want[k]) for k in R._POP_KEYS})

    # ---------------------------------------------------------------- the table fuel
    def test_the_table_fuels_lhv_comes_from_the_decimal(self):
        src = F.synthetic_source(self.base)
        view = R.calibration_contract("mazda_25t", source=src)
        for f in view.fuel_by_table.values():
            self.assertEqual(struct.pack("<d", f.lhv_j_per_kg), struct.pack("<d", 42.908e6))
        # the control: a decimal whose product by 1e6 is another double
        self.assertNotEqual(1.001 * 1e6, 1.001e6)
        name = R.TABLES["mazda_25t"][0].name
        repo = F.rewrite_contract(self.fresh(), lambda c: c["engines"]["mazda_25t"]["fuel_by_table"][name].__setitem__(
            "lhv_mj_per_kg", 1.001))
        got = R.calibration_contract("mazda_25t", source=F.synthetic_source(repo)).fuel_by_table[name].lhv_j_per_kg
        self.assertEqual(struct.pack("<d", got), struct.pack("<d", 1.001e6))

    def test_the_view_is_read_only(self):
        view = R.calibration_contract("mazda_25t", source=F.synthetic_source(self.base))
        with self.assertRaises(TypeError):
            view.lambda_ref["x"] = 1.0
        with self.assertRaises(dataclasses.FrozenInstanceError):
            view.lam_floor = 0.5
        self.assertEqual(view.k3_seconds, 400)


# ============================================================================ Audit
AUDIT_CODE = r"""
import json, os, sys
root, out, extra, engine, commit, contract_json, contract_md, engine_dir = sys.argv[1:9]
seen = set()
def hook(ev, args):
    if ev == "open" and args and isinstance(args[0], (str, bytes)):
        seen.add(os.path.abspath(os.fsdecode(args[0])))
sys.addaudithook(hook)
sys.path.insert(0, root)
import epa_rows as R
src = R.Source(root=root, engine_dir=engine_dir, contract_json=contract_json, contract_md=contract_md,
               contract_commit=commit, allow_poisoned_tables=False)
R.calibration_rows(engine, source=src)
R.calibration_contract(engine, source=src)
R.engine_facts(engine, source=src)
R.manifest(engine, source=src)
R.calibration_coverage(engine, source=src)
if extra:
    open(extra, "rb").close()
with open(out, "w") as fh:
    json.dump(sorted(seen), fh)
"""


class Audit(F.SyntheticRepoCase):
    """The loader's runtime audit (plan 4.6 item 8, at the loader; calibrate_epa.py dry-load's is
    test_calibrate_epa.py's): what it opens, seen by an audit hook in its own process."""

    def opened(self, engine, extra):
        out = os.path.join(tempfile.mkdtemp(dir=self._tmp.name), "opened.json")
        src = F.synthetic_source(self.base)
        r = subprocess.run([sys.executable, "-I", "-B", "-c", AUDIT_CODE, self.base.root, out, extra, engine,
                            src.contract_commit, src.contract_json, src.contract_md, src.engine_dir], capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr.decode(errors="replace")[-2000:])
        with open(out, encoding="utf-8") as fh:
            return json.load(fh), out

    def rel(self, path):
        return os.path.relpath(path, self.base.root).replace(os.sep, "/")

    def outside(self, engine, paths, out):
        src = F.synthetic_source(self.base)
        root = os.path.normcase(os.path.abspath(self.base.root)) + os.sep
        py = {os.path.normcase(os.path.abspath(p)) + os.sep for p in (sys.base_prefix, sys.prefix)}
        allowed = {self.rel(R.table_path(s, source=src)) for s in R.TABLES[engine]}
        allowed |= {self.rel(os.path.join(F.engine_folder(self.base.root, engine), "epa_engine.json")),
                    self.rel(src.contract_json), self.rel(src.contract_md), "engine_thresholds.py",
                    self.rel(os.path.join(os.path.dirname(src.contract_json), os.path.splitext(
                        os.path.basename(src.contract_json))[0], "ecu", "k3_nominal.json"))}
        bad = []
        for p in paths:
            n = os.path.normcase(p)
            if n == os.path.normcase(out) or any(n.startswith(x) for x in py):
                continue
            if not n.startswith(root):
                bad.append(p)
                continue
            rel = self.rel(p)
            if rel in allowed or (rel.startswith("thresholds/") and rel.count("/") == 1) or (
                    rel.endswith(".py") and "/" not in rel) or "__pycache__" in rel:
                continue
            bad.append(rel)
        return bad

    def test_the_loader_opens_only_its_own_engines_files(self):
        for engine in ENGINES:
            paths, out = self.opened(engine, "")
            self.assertEqual(self.outside(engine, paths, out), [], engine)
            mine = {self.rel(p) for p in paths}
            for s in R.TABLES[engine]:                                          # the hook sees the tables
                self.assertIn(self.rel(R.table_path(s, source=F.synthetic_source(self.base))), mine)

    def test_the_control_an_extra_open_is_flagged(self):
        extra = os.path.join(F.engine_folder(self.base.root, "mazda_25t"), "epa_channels.csv")
        paths, out = self.opened("mazda_25t", extra)
        self.assertEqual(self.outside("mazda_25t", paths, out), [self.rel(extra)])
        other = R.table_path(R.TABLES["honda_l15b7"][0], source=F.synthetic_source(self.base))
        paths, out = self.opened("mazda_25t", other)
        self.assertEqual(len(self.outside("mazda_25t", paths, out)), 1)


# ============================================================================ Structural
def same(a, b):
    """Equality by canonical JSON, so a failure message can name what without printing a value."""
    return R.canonical_sha256(a) == R.canonical_sha256(b)


class Structural(unittest.TestCase):
    """The real tables: the only class that opens them. Booleans and counts only; every
    assertion's message names what was compared, never a value."""

    @classmethod
    def setUpClass(cls):
        cls.src = R.Source.repository()
        cls.tmp = tempfile.TemporaryDirectory(prefix="epa_structural_")
        cls.addClassCleanup(cls.tmp.cleanup)

    def test_the_guards_pass(self):
        chk = R.check_contract(source=self.src)
        self.assertTrue(chk.schema == R.CONTRACT_SCHEMA and chk.commit == R.CONTRACT_COMMIT, "contract")
        for eng in ENGINES:
            self.assertTrue(R.check_tables(eng, source=self.src) == R.TABLES[eng], eng)

    def test_the_headers_are_the_pinned_ones(self):
        for eng in ENGINES:
            for spec in R.TABLES[eng]:
                self.assertTrue(tuple(R._header_of(R.table_path(spec, source=self.src)))
                                == R.HEADERS[(eng, spec.role, spec.index)], spec.name)

    def test_counts_and_partition_by_keys(self):
        for eng in ENGINES:
            y = R.calibration_rows(eng, source=self.src)
            view = R.calibration_contract(eng, source=self.src)
            H = R.held_out_keys(eng, source=self.src)
            held = {(t, s) for t, rows in H.items() for s in rows}
            self.assertTrue(y.counts == view.table_counts, f"{eng}: the counts are the contract's")
            self.assertTrue(not (keys_of(y.rows) & held), f"{eng}: yielded and H disjoint")
            for t in y.counts:
                ids = {(t.name, s) for s in range(R.FIRST_DATA_ROW, R.FIRST_DATA_ROW + t.rows)}
                mine = {k for k in keys_of(y.rows) | held if k[0] == t.name}
                self.assertTrue(mine == ids, f"{t.name}: yielded and H are every id")
            self.assertTrue(not ({r.line for r in y.rows} & set(view.held_out_lines)), f"{eng}: no yielded line in L")

    def test_the_calibration_coverage_is_the_contracts(self):
        for eng in ENGINES:
            view = R.calibration_contract(eng, source=self.src)
            got = R.calibration_coverage(eng, source=self.src)
            self.assertTrue(same(got["calibration_fired"], view.coverage_calibration_fired), f"{eng}: fired coverage")
            self.assertTrue(same(got["calibration_hot"], view.coverage_calibration_hot), f"{eng}: hot coverage")

    def test_split_compute_reproduces_split_json(self):
        """The one read of the generator's split.compute here (rule N5's sanctioned exception, plan 4.6 item
        2): the generator's own code converts every row in memory, held-out rows included, and only the
        sha256 of its JSON leaves it; nothing it computes is read, kept or printed (WP3's second fix of 23
        October 2026 records the exception, on the isolation review's finding; WP3_INTERFACES.md 1.1)."""
        chk = R.check_contract(source=self.src)
        text = json.dumps(split.compute(), indent=1, ensure_ascii=True)
        self.assertTrue(hashlib.sha256(text.encode("utf-8")).hexdigest() == chk.generator_inputs["split.json"],
                        "split.compute() is split.json")

    def test_poisoned_held_out_cells_move_neither_the_yield_nor_the_manifest(self):
        for eng in ENGINES:
            y0 = R.calibration_rows(eng, source=self.src)
            for how in R.POISONS:
                dst = tempfile.mkdtemp(dir=self.tmp.name)
                ps = R.poisoned_tables(eng, source=self.src, dst_dir=dst, how=how)
                y = R.calibration_rows(eng, source=ps)
                self.assertTrue(y.sha256 == y0.sha256, f"{eng} {how}: the yield")
                self.assertTrue(R.manifest(eng, source=ps).sha256 == y0.manifest.sha256, f"{eng} {how}: the manifest")
                moved = sum(common.sha_raw(R.table_path(s, source=ps)) != common.sha_raw(R.table_path(s, source=self.src))
                            for s in R.TABLES[eng])
                self.assertTrue(moved == len(R.TABLES[eng]), f"{eng} {how}: every copy carries the poison")
                shutil.rmtree(dst)

    def test_the_printed_lambda_ref_and_floor_move_no_calibration_population(self):
        """split.compute classifies every row with the unrounded lambda_ref and hot floor and prints them
        rounded (to 0.001 and 0.01); the loader classifies with the printed values (plan 4.1). NOTHING OF
        THE GENERATOR'S IS KEPT (WP3's second fix of 23 October 2026, on the isolation and test reviews'
        finding that this test captured the generator's unrounded all-row floor, which can be a held-out
        row's converted MAP, and used it):
          - the hot floor: no calibration row's population moves anywhere in the printed value's rounding
            interval, view.hot_map_floor_kpa +- 0.005 kPa (a threshold, so its ends and its middle decide),
            on the calibration rows alone;
          - lambda_ref: that interval is no help, since lambda_ref is a median of readings printed to 0.001,
            so the interval's ends are themselves possible values, and they do move calibration rows at the
            band's edges (measured 23 October 2026, counts only: 6 and 8 of the Honda's, 1 and 9 of the
            Ford's). So the generator's classify is wrapped and only a boolean leaves its frame: whether
            every lambda_ref it classifies with is one of the printed doubles. The control: the same boolean
            against the printed values moved by 0.001 is false.
        The held-out rows are the validation's to check against per_held_out_line. The floor's control: a
        floor moved onto a hot calibration row's MAP is seen."""
        views = {eng: R.calibration_contract(eng, source=self.src) for eng in ENGINES}
        printed = {eng: {float(v) for v in views[eng].lambda_ref.values()} for eng in ENGINES}
        moved_by = {eng: {float(v) + 0.001 for v in views[eng].lambda_ref.values()} for eng in ENGINES}
        same, same_moved, seen, current = {}, {}, set(), []
        real_load, real_classify = split.load, split.classify

        def load(eng, fn):
            current[:] = [eng]
            return real_load(eng, fn)

        def classify(r, ref, floor, kind):
            eng = current[0]
            seen.add(eng)
            same[eng] = same.get(eng, True) and ref in printed[eng]
            same_moved[eng] = same_moved.get(eng, True) and ref in moved_by[eng]
            return real_classify(r, ref, floor, kind)
        with mock.patch.object(split, "load", load), mock.patch.object(split, "classify", classify):
            split.compute()
        self.assertTrue(seen == set(ENGINES), "the wrapper saw every engine's classify calls")
        for eng in ENGINES:
            self.assertTrue(same[eng], f"{eng}: every lambda_ref the generator classifies with is a printed one")
            self.assertTrue(not same_moved[eng], f"{eng}: the control, the printed values moved by 0.001")

        def moved(rows, floor_b, refs, floor_a):
            n = 0
            for r in rows:
                if isinstance(r, R.InitialRow):
                    continue
                raw = {"intake_manifold_press_kpa_abs": r.map_kpa, "bmep_bar": r.bmep_bar,
                       "fuel_meter_flow_gps": r.fuel_meter_gps, "exhaust_lambda": r.lam_meas}
                kind = "final" if isinstance(r, R.FinalRow) else "steady"
                n += real_classify(raw, refs[r.table], floor_a, kind) != real_classify(raw, refs[r.table], floor_b, kind)
            return n
        for eng in ENGINES:
            view = views[eng]
            y = R.calibration_rows(eng, source=self.src)
            refs, floor = dict(view.lambda_ref), view.hot_map_floor_kpa
            for df in (-0.005, 0.005):
                self.assertTrue(moved(y.rows, floor + df, refs, floor) == 0,
                                f"{eng}: a calibration population moves within the floor's printed rounding")
            hot = next(r for r in y.rows if isinstance(r, R.SteadyRow) and r.pops.hot and r.map_kpa > floor)
            self.assertTrue(moved(y.rows, hot.map_kpa + 1e-3, refs, floor) > 0,                  # above split.TOL
                            f"{eng}: the control, a floor above a hot row's MAP")


# ============================================================================ CarriedPins
class CarriedPins(unittest.TestCase):
    """HANDOFFS WP3 item 6: test_carried.py's pins against the two reads C3 and C4 allow. One of the two
    sanctioned exceptions to WP3_INTERFACES.md 9.1's guard, with Structural and test_contract_pinned
    (rule N4 as amended there, 23 October 2026, the isolation and test reviews' finding): it reads the real
    contract through the calibration view and the real epa_engine.json through engine_facts (the geometry
    and alpha_fuel), never an EPA table, and every comparison is an assertTrue whose message names the pin,
    never a value."""

    @classmethod
    def setUpClass(cls):
        import test_carried
        cls.T = test_carried
        cls.src = R.Source.repository()

    def test_the_pins_are_the_contracts_and_epa_engine_jsons(self):
        """Every comparison by assertTrue with a message that names it, never a value."""
        import engines
        bits = lambda *x: struct.pack("<" + "d" * len(x), *x)              # noqa: E731
        for eng in ENGINES:
            view = R.calibration_contract(eng, source=self.src)
            facts = R.engine_facts(eng, source=self.src)
            bore, (stroke, label), n_cyl, cr, (octane, _), lam_floor, _, lhv, afr = self.T.OWN_ENGINE[eng]
            self.assertTrue(bits(view.lam_floor) == bits(lam_floor), f"{eng}: lam_floor")
            lo, hi = self.T.LINE_ENDS[eng]
            ends = (float(view.lines[0].split("/")[0]), float(view.lines[-1].split("/")[-1]))
            self.assertTrue(ends == (lo, hi), f"{eng}: LINE_ENDS")
            final = next(s.name for s in R.TABLES[eng] if s.role == "final")
            f = view.fuel_by_table[final]                                   # the fuel the engine runs in use
            self.assertTrue(bits(f.lhv_j_per_kg, f.afr_st) == bits(lhv, afr), f"{eng}: the fuel")
            typed = engines.read_spec(eng)["fuel"]
            self.assertTrue(bits(typed["lhv_j_per_kg"], typed["afr_st"]) == bits(lhv, afr), f"{eng}: the typed fuel")
            self.assertTrue(facts.n_cylinders == n_cyl, f"{eng}: n_cyl")
            self.assertTrue(facts.compression_ratio == cr, f"{eng}: comp_ratio")
            self.assertTrue(math.isclose(facts.bore_mm / 1000.0, bore, rel_tol=1e-12), f"{eng}: bore")
            if label == "PUBLISHED":
                self.assertTrue(math.isclose(facts.stroke_mm / 1000.0, stroke, rel_tol=1e-12), f"{eng}: stroke")
            else:                                                          # the Mazda's, from its displacement
                self.assertTrue(facts.stroke_mm is None, f"{eng}: EPA states no stroke")
                derived = facts.displacement_l * 1e-3 / (n_cyl * (math.pi * (facts.bore_mm / 1000.0) ** 2 / 4.0))
                self.assertTrue(math.isclose(derived, stroke, rel_tol=1e-12), f"{eng}: the derived stroke")
            if eng in ("mazda_25t", "ford_27tt"):                          # FTAG 26864's, printed in the Mazda's file
                mazda = R.engine_facts("mazda_25t", source=self.src)
                self.assertTrue(mazda.alpha_fuel["research_octane_number"] == octane, f"{eng}: octane")
                self.assertTrue(math.isclose(mazda.alpha_fuel["energy_density_MJpkg"] * 1e6, lhv, rel_tol=1e-15),
                                f"{eng}: the LHV against alpha_fuel")

    def test_the_mazdas_table_fuels_are_its_typed_fuel_to_the_bit(self):
        """engines.typed_engine("mazda_25t") refuses an EPA engine before its freeze ("ve_base is
        DERIVED"), so the typed fuel is engines.Fuel of its spec's [fuel], as typed_engine builds it."""
        import engines
        typed = engines.Fuel(**engines.read_spec("mazda_25t")["fuel"])
        view = R.calibration_contract("mazda_25t", source=self.src)
        bits = lambda *x: struct.pack("<" + "d" * len(x), *x)              # noqa: E731
        for name, f in view.fuel_by_table.items():
            self.assertTrue(bits(f.lhv_j_per_kg, f.afr_st) == bits(typed.lhv_j_per_kg, typed.afr_st), name)
        # the control: one ulp on the typed value is seen
        self.assertTrue(bits(math.nextafter(typed.lhv_j_per_kg, 0.0)) != bits(f.lhv_j_per_kg), "one ulp")
        with self.assertRaises(ValueError):
            engines.typed_engine("mazda_25t")


# ============================================================================ Scans
STEP2_CODE = F.STEP2_MODULES
STEP2_TESTS = ("test_contract_pinned.py", "test_epa_rows.py", "test_epa_stats.py", "test_epa_fit.py",
               "test_epa_freeze.py", "test_k3_knee.py", "test_epa_coefficients.py", "test_validate_guards.py",
               "test_d3_rows.py", "test_calibrate_epa.py", "test_epa_plants.py", "test_epa_fixtures.py")
TABLE_WORDS = ("epa_" + "steady", "epa_" + "high" + "load")            # built from parts (C3; wrong claim 10)
DE = "data" + "/" + "engines"                                           # N1's string, built from parts
CJ = "ENGINE_THRESHOLDS" + ".json"                                      # N3's
PLANT = ("engines", "engine_env", "plant", "thermal", "derived", "fingerprint", "evaluate")
ANY = None
SPLIT_HELPERS = {"f", "ok", "lam", "nominal", "merge", "name", "classify", "coverage", "ENG", "LAM_BAND", "LAM_ENR",
                 "TOL", "MIN_CLUSTERS", "MAP_SPLIT", "FIRED_BMEP", "OFF_REF", "MAP_BAND", "NOMINAL_RPM", "__file__"}
# WP3_INTERFACES 3.1, the project imports each module may make: {module: {imported: names or ANY}}.
# __file__ joins epa_rows' two lists: guard 2 hashes the module imported (plan 4.2). validate_epa may
# import the plant modules besides "every module above but calibrate_epa", since it builds the E6
# variant plants (engines.build_candidate, WP3_INTERFACES 5.8.5): this test's reading of the row.
MATRIX = {
    # DATA_FOLDER since WP3's integration (23 October 2026): epa_rows.audit_paths hands calibrate_epa's
    # audit the team's data folder (WP3_INTERFACES 3.3 refuses an open under it), and only epa_rows
    # imports thresholds.common's paths
    "epa_rows": {"thresholds.common": {"REPO", "ENGINE_DIR", "CONTRACT_JSON", "CONTRACT_MD", "OUT_DIR", "sha_raw",
                                       "sha_text", "__file__", "DATA_FOLDER"}, "thresholds.split": SPLIT_HELPERS},
    "epa_stats": {"epa_rows": ANY, "thresholds.contract": {"interp", "T_AMB_C"}, "engines": ANY, "engine_env": ANY},
    "epa_fit": {"epa_rows": ANY, "epa_stats": ANY, "engines": ANY, "plant": ANY, "engine_env": ANY},
    "epa_freeze": {"thresholds.common": {"sha_text", "sha_raw", "write_json", "write_text", "REPO", "CONTRACT_JSON",
                                         "CONTRACT_MD"}, "epa_rows": ANY, "engines": ANY, "fingerprint": ANY,
                   "derived": ANY, "plant": ANY, "engine_env": ANY, "thermal": ANY},
    # d3_rows' pin check only (WP3's fix of 23 October 2026, N11 amended): calibrate_epa.py t0 and fit refuse
    # while a D3 summary column is unpinned, and may name nothing else of d3_rows
    "calibrate_epa": {**{m: ANY for m in ("epa_rows", "epa_stats", "epa_fit", "epa_freeze", "k3_knee",
                                          "epa_coefficients", "engines", "derived")}, "d3_rows": {"unpinned_for"}},
    "k3_knee": {"engine_env": ANY, "engines": ANY, "evaluate": ANY, "thresholds.ecu_shift": {"ECU_LOAD_KPA", "SEL"}},
    "epa_coefficients": {"engine_env": ANY, "engines": ANY, "evaluate": ANY, "plant": ANY,
                         "thresholds.contract": {"T_AMB_C"}},
    "validate_epa": {**{m: ANY for m in ("epa_rows", "epa_stats", "epa_fit", "epa_freeze", "k3_knee",
                                         "epa_coefficients", "d3_rows", "thresholds.common") + PLANT},
                     "thresholds.split": {"compute"}, "thresholds.contract": {"interp"}},
    "d3_rows": {"epa_stats": ANY},
}
NEVER_IMPORTED = {"epa_map", "test_epa_map", "thresholds.alpha_nodes", "thresholds.knee_shift", "thresholds.document",
                  "thresholds.b58_propagation"}
NEVER_CALLED = {("thresholds.contract", n) for n in ("build", "load_inputs", "d3_files", "report", "dumps")} | {
    ("thresholds.split", "run"), ("thresholds.split", "report"), ("thresholds.alpha_nodes", "run"),
    ("thresholds.b58_propagation", "run"), ("thresholds.ecu_shift", "one"), ("thresholds.ecu_shift", "run_all"),
    ("thresholds.common", "printout")}
NO_OPEN = {"epa_stats.py", "epa_fit.py", "calibrate_epa.py", "k3_knee.py", "epa_coefficients.py"}
# N2 (widened by WP3's fix of 23 October 2026, on the isolation review's finding that an alias, an import
# under another name or a getattr passed a scan of call names): every REFERENCE to the held-out readers, a
# name, an attribute, an import of one or a getattr naming one, outside the files allowed each; and a getattr
# on the loader whose name is not a literal, outside them.
HELD_READERS = {"read_held_out": ("validate_epa.py", "test_validate_guards.py"),
                "held_out_counts": ("validate_epa.py", "test_validate_guards.py"),
                "held_out_population_counts": ("validate_epa.py", "test_validate_guards.py"),
                "held_out_keys": ("validate_epa.py", "test_validate_guards.py", "test_epa_rows.py")}
# N12 (WP3's fix of 23 October 2026, the same review: a leak that read the tables through the loader's own
# private readers passed every scan): EVERY underscore-prefixed name of epa_rows (a dunder excepted), named
# nowhere but in epa_rows.py, its two test files and test_calibrate_epa.py, whose Poison tests replay the leak
# (WP3's second fix of 23 October 2026, on the second isolation review's finding that a hand list of readers
# passed _load_json and _engine_block, which read the whole contract).
PRIVATE_ALLOWED = ("epa_rows.py", "test_epa_rows.py", "test_epa_fixtures.py", "test_calibrate_epa.py")


def _private(name):
    return isinstance(name, str) and name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


# N3 widened (the same review: the contract was loaded through the Source's lower-case attribute): the
# attributes of an epa_rows.Source that hold the contract's and the tables' paths, read nowhere in a step-2
# module but the loader and the validation (calibrate_epa.py reaches them through epa_rows' helpers:
# garbled_source, tables_moved, engine_file_path, audit_paths).
SOURCE_PATH_ATTRS = ("contract_json", "contract_md", "engine_dir")
SOURCE_PATH_ALLOWED = ("epa_rows.py", "validate_epa.py")
# N8 widened (the same review: linecache, fileinput and a re-exported io passed OPENERS): the standard
# library's other readers of a path, never imported by a NO_OPEN file, directly or through a re-export.
OPENER_MODULES = ("linecache", "fileinput", "io", "codecs", "pathlib", "shutil", "mmap", "tokenize", "urllib")
# The isolation review's leak (23 October 2026, its scratch leak_poison.py), as source: held-out
# turbine-inlet pressures summed from the repository's own tables through the loader's private readers. It
# passed every scan before N12; test_calibrate_epa.Poison runs its runtime half (the poison's refusal).
LEAK_SRC = """
import epa_rows
def _held_tip_sum(name):
    src = epa_rows.Source.repository()
    c, _ = epa_rows._verified_contract(src)
    held = epa_rows._held_keys(name, c)
    tot = 0.0
    for spec in epa_rows.TABLES[name]:
        for sr, rec in epa_rows._records(spec, epa_rows.table_path(spec, source=src)):
            if sr in held[spec.name]:
                v = epa_rows._cells(spec, rec).get("turbine_inlet_press_kpa_abs", "")
                tot += float(v) if v else 0.0
    return tot
"""
# The second isolation review's contract leak (23 October 2026, its scratch scan_leaks.py, L1): the whole
# contract loaded through the loader's private reader and the Source's lower-case attribute, its held-out keys
# read; it passed every scan before N12 and N3 were widened. test_calibrate_epa.Seal runs its runtime half.
LEAK_CONTRACT_SRC = """
import epa_rows
def s3b_gate(name):
    src = epa_rows.Source.repository()
    c = epa_rows._load_json(src.contract_json)
    return c["engines"][name]["per_held_out_line"]
"""
OPENERS = {"open", "read_text", "read_bytes", "write_text", "write_bytes", "loadtxt", "genfromtxt", "fromfile",
           "getline", "getlines", "updatecache", "FileIO", "load", "memmap", "read_csv"}
# The third isolation review's leaks (24 October 2026, its scratch iso_leaks_test.py), as source: the contract
# through `git show` in a stage, a table through a child interpreter, and the contract through epa_freeze's
# private readers. They passed every scan before N13 and N12's widening; test_calibrate_epa.Seal and Poison run
# their runtime half (the seal over child processes).
LEAK_GIT_SRC = '''
import subprocess, json, os
import epa_rows
def _s1_extra(name):
    root = os.path.dirname(epa_rows.__file__)
    rel = "results/" + "ENGINE_" + "THRESHOLDS" + ".json"
    out = subprocess.run(["git", "show", "HEAD:" + rel], cwd=root, capture_output=True).stdout
    return json.loads(out)["engines"][name]["per_held_out_line"]
'''
LEAK_CHILD_SRC = '''
import subprocess, sys, os
import epa_rows
def _peek(name, spec, sr):
    code = "import csv,os,sys\\np=os.path.join(sys.argv[1],'da'+'ta','eng'+'ines',sys.argv[2],sys.argv[3])\\nprint(1)"
    return subprocess.run([sys.executable, "-I", "-c", code, os.path.dirname(epa_rows.__file__), name, spec.name],
                          capture_output=True, text=True).stdout
'''
LEAK_FREEZE_PRIVATE_SRC = '''
import os
import epa_freeze, epa_rows
def peek(name, source):
    p = epa_rows.audit_paths(name, source=source)["contract"][0]
    return epa_freeze._git(source.root, "show", "HEAD:" + p).stdout
def peek2(name, source):
    p = epa_rows.audit_paths(name, source=source)["contract"][0]
    return epa_freeze._read_json(os.path.join(source.root, p))["engines"][name]["per_held_out_line"]
'''
# N13 (WP3's third fix of 24 October 2026, on the third isolation review's planted leaks: `import subprocess` in
# epa_fit.py or epa_stats.py, epa_freeze's re-exported subprocess, a raw multiprocessing pool with no audit
# initializer and ctypes each passed every scan, and a child process has no audit hook): in a NO_OPEN file, no
# import of a module that makes a process or reaches the system below Python, none of them reached through a
# re-export, no os function that makes a process, no getattr on os, builtins or such a module, and no dynamic
# import or evaluation (a getattr of builtins.open through __import__ passed N8). epa_fit.py imports
# multiprocessing for its ordered pool, and names it only inside the pool's own helper (POOL_HELPERS), whose
# workers the audit's initializer guards (calibrate_epa.Audit._spawn_problem refuses any other spawn while sealed).
PROCESS_MODULES = ("subprocess", "ctypes", "_ctypes", "_winapi", "_posixsubprocess", "concurrent", "multiprocessing",
                   "pty", "builtins", "importlib", "runpy", "code", "msvcrt", "_thread", "threading", "asyncio")
OS_PROCESS = {"system", "popen", "startfile", "fork", "forkpty", "posix_spawn", "posix_spawnp", "kill", "killpg",
              "_exit"}
OS_PROCESS_PREFIXES = ("exec", "spawn")
DYNAMIC_NAMES = ("__import__", "eval", "exec", "compile", "__builtins__")
POOL_HELPERS = {("epa_fit.py", "multiprocessing"): ("_pool",)}
# N12 widened (the same review: epa_freeze's private readers -- _git, _git_ok, _read_json -- read the contract
# through git or whole and passed N12, which named epa_rows' alone): every underscore-prefixed name of these
# modules, outside the module and its own test.
PRIVATE_OF = {"epa_rows": PRIVATE_ALLOWED, "epa_freeze": ("epa_freeze.py", "test_epa_freeze.py")}


def _os_process(attr):
    return isinstance(attr, str) and (attr in OS_PROCESS or attr.startswith(OS_PROCESS_PREFIXES))


def project_modules():
    tops = {os.path.splitext(f)[0] for f in os.listdir(HERE) if f.endswith(".py")}
    tops |= {d for d in os.listdir(HERE) if os.path.isfile(os.path.join(HERE, d, "__init__.py"))}
    return tops


PROJECT = project_modules()


def _is_module(dotted):
    parts = dotted.split(".")
    return os.path.isfile(os.path.join(HERE, *parts) + ".py") or os.path.isfile(os.path.join(HERE, *parts, "__init__.py"))


_REEXPORTS = {}


def reexports(dotted):
    """{name: module} of the modules a project module binds at its top level (import x; import x as y; from a
    import b where a.b is a module), so that an attribute chain through it -- epa_rows.split.load,
    epa_rows.common, epa_rows.io -- resolves to the module it reaches (WP3's second fix of 23 October 2026, on
    the second isolation review's finding that the import matrix and N5 passed epa_rows.split.load). {} for a
    module that is not the project's."""
    if dotted in _REEXPORTS:
        return _REEXPORTS[dotted]
    parts = dotted.split(".")
    path = os.path.join(HERE, *parts) + ".py"
    if not os.path.isfile(path):
        path = os.path.join(HERE, *parts, "__init__.py")
    out = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())

        def walk(body):
            for node in body:
                if isinstance(node, ast.Import):
                    for a in node.names:
                        out[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
                elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                    for a in node.names:
                        full = f"{node.module}.{a.name}"
                        if _is_module(full) or _stdlib_module(full):
                            out[a.asname or a.name] = full
                elif isinstance(node, (ast.If, ast.Try)):
                    walk(node.body)
                    walk(getattr(node, "orelse", []))
                    for h in getattr(node, "handlers", []):
                        walk(h.body)
        walk(tree.body)
    _REEXPORTS[dotted] = out
    return out


def _stdlib_module(dotted):
    """Whether `dotted` names a module of the standard library (os.path, xml.etree, ...), looked up without
    importing any third-party package."""
    import importlib.util
    if dotted.split(".")[0] not in sys.stdlib_module_names:
        return False
    try:
        return importlib.util.find_spec(dotted) is not None
    except (ImportError, ValueError):
        return False


class _Scan(ast.NodeVisitor):
    """The bindings of one file and every node the rules look at, with the enclosing class and
    function of each."""

    def __init__(self, tree):
        self.bind = {}                     # local name -> (module, attribute or None)
        self.imports = []                  # (module, names or None, line)
        self.calls, self.names, self.strings, self.keys, self.stack = [], [], [], [], []
        self.docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
                b = node.body[0]
                if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                    self.docstrings.add(id(b.value))
        self.visit(tree)

    def where(self):
        return tuple(self.stack)

    def visit_ClassDef(self, node):
        self.stack.append(("class", node.name))
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node):
        self.stack.append(("def", node.name))
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Import(self, node):
        for a in node.names:
            self.imports.append((a.name, None, node.lineno))
            if a.asname:
                self.bind[a.asname] = (a.name, None)
            else:
                self.bind[a.name.split(".")[0]] = (a.name.split(".")[0], None)

    def visit_ImportFrom(self, node):
        if node.level or not node.module:
            return
        for a in node.names:
            full = f"{node.module}.{a.name}"
            if _is_module(full):
                self.imports.append((full, None, node.lineno))
                self.bind[a.asname or a.name] = (full, None)
            else:
                self.imports.append((node.module, {a.name}, node.lineno))
                self.bind[a.asname or a.name] = (node.module, a.name)

    def resolve(self, expr):
        """(module, attribute) a Name or a Name.attr refers to, or None. An attribute that is a module the
        named module binds itself (reexports) resolves to that module, along a chain of any length."""
        if isinstance(expr, ast.Name) and expr.id in self.bind:
            return self.bind[expr.id]
        if isinstance(expr, ast.Attribute) and isinstance(expr.value, (ast.Name, ast.Attribute)):
            inner = self.resolve(expr.value)
            if inner and inner[1] is None:
                mod = inner[0]
                sub = f"{mod}.{expr.attr}"
                if _is_module(sub):
                    return sub, None
                via = reexports(mod).get(expr.attr)
                if via is not None:
                    return via, None
                return mod, expr.attr
        return None

    def visit_Call(self, node):
        self.calls.append((node, self.where()))
        self.generic_visit(node)

    def visit_Name(self, node):
        self.names.append((node.id, node, self.where()))

    def visit_Attribute(self, node):
        self.names.append((node.attr, node, self.where()))
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str) and id(node) not in self.docstrings:
            self.strings.append((node.value, node, self.where()))

    def visit_Subscript(self, node):
        s = node.slice
        if isinstance(s, ast.Constant) and isinstance(s.value, str):
            self.keys.append((s.value, node, self.where()))
        self.generic_visit(node)

    def visit_Dict(self, node):
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                self.keys.append((k.value, node, self.where()))
        self.generic_visit(node)


def _callee_name(call):
    f = call.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def _in(where, kind, name):
    return (kind, name) in where


def _at_arm(where):
    """Inside validate_epa's arm step: the function arm, or a helper of its own named _arm*
    (this test's reading of N5's "validate_epa.arm"; a call from run or any other step is not)."""
    return any(k == "def" and (n == "arm" or n.startswith("_arm")) for k, n in where)


def scan_source(src, rel):
    """[(rule, line, detail)] for every rule of WP3_INTERFACES 3.1 and 3.2 that `src`, the file
    `rel`, breaks. rel decides what the file is allowed (a step-2 module, a test, which one)."""
    tree = ast.parse(src)
    s = _Scan(tree)
    base = os.path.basename(rel)
    mod = os.path.splitext(base)[0]
    is_test = base.startswith("test_")
    out = []

    def flag(rule, node, detail):
        out.append((rule, getattr(node, "lineno", 0), detail))
    # 3.1: the matrix, and what no step-2 file imports
    for imp, names, line in s.imports:
        top = imp.split(".")[0]
        if imp in NEVER_IMPORTED or any(imp.startswith(n + ".") for n in NEVER_IMPORTED):
            out.append(("3.1 never", line, imp))
        if imp == "validate_epa" and base != "test_validate_guards.py":
            out.append(("N10", line, imp))
        if imp == "d3_rows" and base not in ("validate_epa.py", "test_d3_rows.py", "test_epa_fixtures.py",
                                             "calibrate_epa.py", "test_calibrate_epa.py", "test_validate_guards.py"):
            out.append(("N11", line, imp))
        if imp == "epa_rows" and names:
            for nm in names:
                if nm in HELD_READERS and base not in HELD_READERS[nm] and base != "epa_rows.py":
                    out.append(("N2", line, f"from epa_rows import {nm}"))
                if _private(nm) and base not in PRIVATE_ALLOWED:
                    out.append(("N12", line, f"from epa_rows import {nm}"))
        if base in NO_OPEN and top in OPENER_MODULES:
            out.append(("N8", line, f"import {imp}"))
        if mod in MATRIX and top in PROJECT:
            allowed = MATRIX[mod]
            if imp not in allowed:
                out.append(("3.1 matrix", line, imp))
            elif allowed[imp] is not ANY and names is not None and not names <= allowed[imp]:
                out.append(("3.1 matrix", line, f"{imp}: {sorted(names - allowed[imp])}"))
    imported = {imp for imp, _, _ in s.imports}
    if mod in MATRIX:
        for nm, node, _ in s.names:
            if isinstance(node, ast.Attribute):
                r = s.resolve(node)
                if r and r[1] and r[0] in MATRIX[mod] and MATRIX[mod][r[0]] is not ANY and r[1] not in MATRIX[mod][r[0]]:
                    flag("3.1 matrix", node, f"{r[0]}.{r[1]}")
                # a project module reached through another's re-export, which no import of this file names
                if r and r[0] != mod and r[0].split(".")[0] in PROJECT and r[0] not in MATRIX[mod] and r[0] not in imported:
                    flag("3.1 matrix", node, f"{r[0]} reached through a re-export")
    for nm, node, _ in s.names:
        if isinstance(node, ast.Attribute) and base in NO_OPEN:
            r = s.resolve(node)
            if r and r[0].split(".")[0] in OPENER_MODULES and r[0] not in imported:
                flag("N8", node, f"{r[0]} reached through a re-export")
    # N13: no child process, no reach below Python, no dynamic import, in a NO_OPEN file
    if base in NO_OPEN:
        def pool_helper(top, where):
            return any(_in(where, "def", fn) for fn in POOL_HELPERS.get((base, top), ()))
        for imp, names, line in s.imports:
            top = imp.split(".")[0]
            if top in PROCESS_MODULES and (base, top) not in POOL_HELPERS:
                out.append(("N13", line, f"import {imp}"))
            if imp == "os" and names and any(_os_process(n) for n in names):
                out.append(("N13", line, f"from os import {sorted(n for n in names if _os_process(n))}"))
        for nm, node, where in s.names:
            r = s.resolve(node) if isinstance(node, ast.Attribute) else s.bind.get(nm)
            if r is not None:
                top = r[0].split(".")[0]
                if top in PROCESS_MODULES and not pool_helper(top, where):
                    flag("N13", node, r[0] + (f".{r[1]}" if r[1] else ""))
                elif r[0] == "os" and _os_process(r[1]):
                    flag("N13", node, f"os.{r[1]}")
            if isinstance(node, ast.Name) and nm in DYNAMIC_NAMES:
                flag("N13", node, nm)
        for call, where in s.calls:
            if _callee_name(call) == "getattr" and call.args:
                r0 = s.resolve(call.args[0])
                if r0 is not None and r0[1] is None and (r0[0] == "os" or r0[0].split(".")[0] in PROCESS_MODULES):
                    flag("N13", call, f"getattr({r0[0]}, ...)")
    # N12 widened to epa_freeze's private names (PRIVATE_OF), outside epa_freeze.py and its test
    for mod_name, allowed_in in PRIVATE_OF.items():
        if mod_name == "epa_rows" or base in allowed_in:
            continue
        for imp, names, line in s.imports:
            if imp == mod_name and names:
                out += [("N12", line, f"from {mod_name} import {n}") for n in sorted(names) if _private(n)]
        for nm, node, _ in s.names:
            if _private(nm) and isinstance(node, ast.Attribute):
                r = s.resolve(node)
                if r is not None and r[0] == mod_name and r[1] == nm:
                    flag("N12", node, f"{mod_name}.{nm}")
        for call, _ in s.calls:
            if _callee_name(call) == "getattr" and call.args and s.resolve(call.args[0]) == (mod_name, None):
                a1 = call.args[1] if len(call.args) > 1 else None
                lit = a1.value if isinstance(a1, ast.Constant) and isinstance(a1.value, str) else None
                if lit is None or _private(lit):
                    flag("N12", call, f"getattr({mod_name}, {lit!r})")
    # calls
    for call, where in s.calls:
        r = s.resolve(call.func)
        name = _callee_name(call)
        if name == "getattr" and call.args and s.resolve(call.args[0]) == ("epa_rows", None) and base != "epa_rows.py":
            a1 = call.args[1] if len(call.args) > 1 else None
            lit = a1.value if isinstance(a1, ast.Constant) and isinstance(a1.value, str) else None
            if lit is None and base not in PRIVATE_ALLOWED + ("validate_epa.py", "test_validate_guards.py"):
                flag("N2", call, "getattr(epa_rows, <not a literal>)")
            elif lit in HELD_READERS and base not in HELD_READERS[lit]:
                flag("N2", call, f"getattr(epa_rows, {lit!r})")
            elif _private(lit) and base not in PRIVATE_ALLOWED:
                flag("N12", call, f"getattr(epa_rows, {lit!r})")
        if r in NEVER_CALLED:
            flag("N5/C12", call, f"{r[0]}.{r[1]}")
        if r in {("thresholds.split", "compute"), ("thresholds.split", "load")}:
            ok = (base == "validate_epa.py" and r[1] == "compute" and _at_arm(where)) or (
                base == "test_epa_rows.py" and _in(where, "class", "Structural"))
            if not ok:
                flag("N5", call, f"{r[0]}.{r[1]}")
        if r in {("thresholds.common", "write_json"), ("thresholds.common", "write_text")} and base != "epa_freeze.py":
            flag("N6", call, r[1])
        if name in ("read_held_out", "held_out_counts", "held_out_population_counts") and base not in (
                "validate_epa.py", "test_validate_guards.py"):
            flag("N2", call, name)
        if name == "held_out_keys" and base not in ("validate_epa.py", "test_validate_guards.py", "test_epa_rows.py"):
            flag("N2", call, name)
        if base in NO_OPEN and name in OPENERS and (isinstance(call.func, ast.Attribute) or name == "open"):
            flag("N8", call, name)
        for kw in call.keywords:
            if kw.arg == "allow_poisoned_tables" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                if not (is_test or base in ("calibrate_epa.py", "epa_rows.py")):
                    flag("N7", call, "allow_poisoned_tables=True")
        if is_test and name == "repository":
            ok = (base == "test_epa_rows.py" and (_in(where, "class", "Structural") or _in(where, "class", "CarriedPins"))
                  ) or base == "test_contract_pinned.py"
            if not ok:
                flag("N4", call, "Source.repository()")
        if is_test and name in ("Source", "replace") and base not in ("test_contract_pinned.py",):
            for a in list(call.args) + [k.value for k in call.keywords]:
                for sub in ast.walk(a):
                    nm = sub.id if isinstance(sub, ast.Name) else sub.attr if isinstance(sub, ast.Attribute) else None
                    if nm in ("REPO", "ENGINE_DIR", "CONTRACT_JSON", "CONTRACT_MD"):
                        flag("N4", call, f"{name}(... {nm} ...)")
    # names
    for nm, node, where in s.names:
        if nm in HELD_READERS and base not in HELD_READERS[nm] and base != "epa_rows.py":
            flag("N2", node, nm)
        if _private(nm) and base not in PRIVATE_ALLOWED:
            r = s.resolve(node) if isinstance(node, ast.Attribute) else s.bind.get(nm)
            if r is not None and r[0] == "epa_rows" and (r[1] == nm or (r[1] is None and nm == "epa_rows")):
                flag("N12", node, nm)
        if (nm in SOURCE_PATH_ATTRS and isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)
                and not is_test and base not in SOURCE_PATH_ALLOWED):
            flag("N3", node, f"a Source's {nm}")
        if nm in ("ENGINE_DIR", "ENGINES_DIR") and base not in ("epa_rows.py", "test_epa_fixtures.py"):
            flag("N1", node, nm)
        if nm in ("Token", "verify_for_validation") and base not in ("validate_epa.py", "test_validate_guards.py"):
            flag("N2", node, nm)
        if nm in ("CONTRACT_JSON", "CONTRACT_MD"):
            if base in ("epa_rows.py", "validate_epa.py", "test_contract_pinned.py", "test_epa_fixtures.py"):
                continue
            if base == "epa_freeze.py" and _is_sha_text_arg(s, node):
                continue
            flag("N3", node, nm)
    for text, node, where in s.strings:
        if (DE in text or DE.replace("/", "\\") in text) and base not in ("epa_rows.py", "test_epa_fixtures.py"):
            flag("N1", node, "a string naming the tables' folder")
        if CJ in text and base not in ("epa_rows.py", "validate_epa.py", "test_contract_pinned.py",
                                                             "test_epa_fixtures.py"):
            if not (base == "epa_freeze.py" and _is_sha_text_arg(s, node)):
                flag("N3", node, "the contract's file name")
    for key, node, where in s.keys:
        if key == "tables" and base not in ("epa_rows.py", "test_epa_fixtures.py"):
            flag("N1", node, '"tables" as a key')
    for call, where in s.calls:
        if _callee_name(call) == "get" and call.args and isinstance(call.args[0], ast.Constant) and \
                call.args[0].value == "tables" and base not in ("epa_rows.py", "test_epa_fixtures.py"):
            flag("N1", call, '"tables" as a key')
    return out


def _is_sha_text_arg(s, node):
    """Whether node is an argument of a call to sha_text (epa_freeze's one use of the contract)."""
    for call, _ in s.calls:
        if _callee_name(call) == "sha_text" and any(node is a or any(node is x for x in ast.walk(a)) for a in call.args):
            return True
    return False


def scan_words(src, rel):
    """N9: the table names, built from parts, in a .py that is not epa_map.py, test_epa_map.py or
    the generator (the generator's own claim, thresholds/document.py)."""
    if rel in ("epa_map.py", "test_epa_map.py", "engine_thresholds.py") or rel.startswith("thresholds/"):
        return []
    return [("N9", 0, w) for w in TABLE_WORDS if w in src]


# WP3_INTERFACES.md 9.1: every test class runs inside forbid_real_data but the ones named there (WP3's second fix
# of 23 October 2026, on the test review's finding that three classes ran unguarded and only test_epa_fit checked
# its own file): a class that derives (in its file) from unittest.TestCase must reach a guarded base --
# test_epa_fixtures' Guarded or SyntheticRepoCase, or a class of its own file whose body enters
# forbid_real_data -- unless it is named here, or its file keeps its own module-level hook.
GUARDED_BASES = ("Guarded", "SyntheticRepoCase")
GUARD_EXEMPT = {("test_epa_rows.py", "Structural"), ("test_epa_rows.py", "CarriedPins")}
# test_contract_pinned reads the real contract and the generator's outputs by design (plan 8.4), every class
GUARD_EXEMPT_FILES = ("test_contract_pinned.py",)
OWN_HOOK_FILES = ("test_epa_stats.py",)


def unguarded_test_classes(src, rel):
    """The test classes of `src` (the file `rel`) that reach unittest.TestCase without a guarded base, the
    exemptions above left out."""
    tree = ast.parse(src)
    base = os.path.basename(rel)
    defs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    memo = {}

    def status(name):
        if name in memo:
            return memo[name]
        memo[name] = None
        node, out = defs[name], None
        for b in node.bases:
            text = ast.unparse(b)
            short = text.split(".")[-1]
            if short in GUARDED_BASES and short not in defs:
                out = "guarded"
                break
            if short in defs:
                st = status(short)
                if st == "guarded":
                    out = "guarded"
                    break
                out = out or st
            elif text in ("unittest.TestCase", "TestCase"):
                out = out or "testcase"
        if out == "testcase" and "forbid_real_data" in ast.unparse(node):
            out = "guarded"
        memo[name] = out
        return out
    if base in GUARD_EXEMPT_FILES:
        return []
    if base in OWN_HOOK_FILES:
        return [] if ("sys.addaudithook" in src and "_hook" in src) else ["<the file's own hook is missing>"]
    return sorted(n for n in defs if status(n) == "testcase" and (base, n) not in GUARD_EXEMPT)


def committed_py():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"], cwd=HERE,
                         capture_output=True, text=True, check=True).stdout.splitlines()
    return sorted(set(out))


def read(rel):
    with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
        return fh.read()


class Scans(F.Guarded):
    def test_every_test_class_runs_guarded(self):
        """Every step-2 test file's classes run inside forbid_real_data (WP3_INTERFACES.md 9.1), but the named
        exceptions; the control: a scratch class on unittest.TestCase is found, and one on Guarded is not."""
        hits = {rel: unguarded_test_classes(read(rel), rel) for rel in STEP2_TESTS if os.path.isfile(os.path.join(HERE, rel))}
        self.assertEqual({k: v for k, v in hits.items() if v}, {})
        bad = "import unittest\nclass Loose(unittest.TestCase):\n    pass\nclass Child(Loose):\n    pass\n"
        self.assertEqual(unguarded_test_classes(bad, "test_epa_fit.py"), ["Child", "Loose"])
        good = "import test_epa_fixtures as F\nclass Tight(F.Guarded):\n    pass\n"
        self.assertEqual(unguarded_test_classes(good, "test_epa_fit.py"), [])
        self.assertEqual(unguarded_test_classes(bad, "test_epa_stats.py"), ["<the file's own hook is missing>"])

    def test_every_step2_file_keeps_every_rule(self):
        hits = []
        for rel in STEP2_CODE + STEP2_TESTS:
            if os.path.isfile(os.path.join(HERE, rel)):
                hits += [(rel,) + h for h in scan_source(read(rel), rel)]
        self.assertEqual(hits, [])

    def test_no_py_names_the_tables(self):
        hits = []
        for rel in committed_py():
            try:
                hits += [(rel,) + h for h in scan_words(read(rel), rel)]
            except (OSError, UnicodeDecodeError):
                continue
        self.assertEqual(hits, [])

    def flagged(self, rule, src, rel):
        return [h for h in scan_source(src, rel) if h[0] == rule]

    def test_each_rule_can_fail(self):
        """Each rule on a scratch source that breaks it (mistake 12), and where it says so, the
        same source in the file it is allowed in."""
        cases = [
            ("3.1 never", "import epa_" + "map\n", "epa_fit.py", None),
            ("3.1 never", "from thresholds import b58_propagation\n", "test_epa_fit.py", None),
            ("3.1 matrix", "import plant\n", "epa_stats.py", "epa_fit.py"),
            ("3.1 matrix", "from thresholds import split\n", "epa_fit.py", "epa_rows.py"),
            ("3.1 matrix", "from thresholds.split import load\n", "epa_rows.py", None),
            ("3.1 matrix", "from thresholds import split\nsplit.compute()\n", "epa_rows.py", None),
            ("3.1 matrix", "import epa_freeze\n", "k3_knee.py", "calibrate_epa.py"),
            ("N10", "import validate_epa\n", "calibrate_epa.py", "test_validate_guards.py"),
            ("N11", "import d3_rows\n", "epa_stats.py", "test_d3_rows.py"),
            ("N5", "from thresholds import split\nsplit.compute()\n", "test_epa_stats.py", None),
            ("N5", "from thresholds import split\ndef run():\n    split.compute()\n", "validate_epa.py", None),
            ("N5/C12", "from thresholds import common\ncommon.printout('x')\n", "test_epa_fit.py", None),
            ("N5/C12", "from thresholds.contract import build\nbuild(1, 2, 3)\n", "validate_epa.py", None),
            ("N6", "from thresholds import common\ncommon.write_json('p', {})\n", "calibrate_epa.py", "epa_freeze.py"),
            ("N2", "import epa_rows\nepa_rows.read_held_out('x', source=1, token=2)\n", "test_epa_stats.py",
             "test_validate_guards.py"),
            ("N2", "import epa_rows\nepa_rows.held_out_counts('x', source=1)\n", "calibrate_epa.py", "validate_epa.py"),
            ("N2", "import epa_rows\nepa_rows.held_out_keys('x', source=1)\n", "calibrate_epa.py", "test_epa_rows.py"),
            # N2 widened (WP3's fix of 23 October 2026): an alias, an import under another name, a getattr
            ("N2", "import epa_rows\nf = epa_rows.held_out_counts\nf('x', source=1)\n", "epa_fit.py", "validate_epa.py"),
            ("N2", "from epa_rows import held_out_counts as hc\nhc('x', source=1)\n", "epa_fit.py", "validate_epa.py"),
            ("N2", "import epa_rows\ngetattr(epa_rows, 'held_' + 'out_counts')('x', source=1)\n", "epa_fit.py",
             "validate_epa.py"),
            ("N2", "import epa_rows\nr = epa_rows.read_held_out\n", "calibrate_epa.py", "test_validate_guards.py"),
            # N12: the loader's private readers, and the isolation review's leak, which read through them
            ("N12", "import epa_rows\nepa_rows._records(1, 2)\n", "epa_fit.py", "test_epa_fixtures.py"),
            ("N12", "from epa_rows import _held_keys\n", "calibrate_epa.py", "test_epa_rows.py"),
            ("N12", "import epa_rows\ngetattr(epa_rows, '_cells')\n", "epa_stats.py", "test_epa_rows.py"),
            ("N12", LEAK_SRC, "epa_fit.py", None),
            ("N12", LEAK_SRC, "calibrate_epa.py", None),
            # N11 amended: calibrate_epa imports d3_rows for its pin check and names nothing else of it
            ("3.1 matrix", "import d3_rows\nd3_rows.read_summary('x', spec=1)\n", "calibrate_epa.py", "validate_epa.py"),
            ("N2", "import epa_rows\nepa_rows.held_out_population_counts('x', source=1)\n", "calibrate_epa.py",
             "validate_epa.py"),
            ("3.1 matrix", "from thresholds import common\ncommon.DATA_FOLDER\n", "epa_stats.py", "epa_rows.py"),
            ("N2", "Token = 1\n", "epa_freeze.py", "validate_epa.py"),
            ("N8", "open('x')\n", "epa_fit.py", "epa_freeze.py"),
            ("N8", "import pathlib\npathlib.Path('x').read_text()\n", "k3_knee.py", "d3_rows.py"),
            ("N7", "import epa_rows\nepa_rows.Source(allow_poisoned_tables=True)\n", "epa_fit.py", "calibrate_epa.py"),
            ("N4", "import epa_rows\nepa_rows.Source.repository()\n", "test_epa_fit.py", "test_contract_pinned.py"),
            ("N4", "import epa_rows\nclass Synthetic:\n    def t(self):\n        epa_rows.Source.repository()\n",
             "test_epa_rows.py", None),
            ("N4", "import epa_rows\nfrom thresholds import common\nepa_rows.Source(root=common.REPO)\n",
             "test_validate_guards.py", None),
            ("N1", "from thresholds import common\ncommon.ENGINE_DIR\n", "epa_freeze.py", "epa_rows.py"),
            ("N1", f"q = '{DE}/x'\n", "validate_epa.py", "test_epa_fixtures.py"),
            ("N1", "c = {}\nc['tables']\n", "epa_fit.py", "epa_rows.py"),
            ("N1", "c = {}\nc.get('tables')\n", "validate_epa.py", "epa_rows.py"),
            ("N3", "from thresholds import common\ncommon.CONTRACT_JSON\n", "epa_fit.py", "validate_epa.py"),
            ("N3", f"x = 'results/{CJ}'\n", "test_epa_stats.py", "test_contract_pinned.py"),
            ("N3", "from thresholds import common\nx = common.CONTRACT_JSON\n", "epa_freeze.py", None),
            # the second isolation review's leaks (23 October 2026, its scratch scan_leaks.py and scan_leaks2.py),
            # each of which gave no hit before the scans were widened
            ("N12", LEAK_CONTRACT_SRC, "epa_fit.py", None),
            ("N3", LEAK_CONTRACT_SRC, "epa_fit.py", "validate_epa.py"),
            ("N12", "import epa_rows\ndef h(name):\n    src = epa_rows.Source.repository()\n"
                    "    return epa_rows._engine_block(epa_rows._load_json(src.contract_json), name)['held_out_rows']\n",
             "epa_stats.py", "test_epa_fixtures.py"),
            ("N5", "import epa_rows\ndef all_rows(name):\n    return [epa_rows.split.load(name, t.name) "
                   "for t in epa_rows.TABLES[name]]\n", "epa_fit.py", None),
            ("N5", "import epa_rows\ndef all_rows():\n    return epa_rows.split.compute()\n", "calibrate_epa.py", None),
            ("3.1 matrix", "import epa_rows\ndef all_rows():\n    return epa_rows.split.compute()\n", "epa_stats.py",
             None),
            ("3.1 matrix", "import epa_rows\ndef c():\n    return epa_rows.common.load_json('x')\n", "epa_fit.py", None),
            ("N8", "import epa_rows, linecache\ndef rows(name):\n    src = epa_rows.Source.repository()\n"
                   "    return [linecache.getlines(epa_rows.table_path(t, source=src)) for t in epa_rows.TABLES[name]]\n",
             "epa_fit.py", "d3_rows.py"),
            ("N8", "import epa_rows, fileinput, os\ndef rows(name):\n    src = epa_rows.Source.repository()\n"
                   "    return list(fileinput.input(os.path.join(src.engine_dir, name, 'epa_engine.json')))\n",
             "epa_stats.py", "d3_rows.py"),
            ("N3", "import epa_rows, fileinput, os\ndef rows(name):\n    src = epa_rows.Source.repository()\n"
                   "    return list(fileinput.input(os.path.join(src.engine_dir, name, 'epa_engine.json')))\n",
             "epa_stats.py", "validate_epa.py"),
            ("N8", "import epa_rows\ndef rows(p):\n    return epa_rows.io.FileIO(p).read()\n", "epa_fit.py", "d3_rows.py"),
            ("N3", "import epa_freeze\ndef peek(name, source):\n"
                   "    c = epa_freeze.read_json(source.contract_json, root=source.root)\n"
                   "    return c['engines'][name]['coverage']\n", "calibrate_epa.py", "validate_epa.py"),
            ("N12", "import os, epa_rows\ndef alpha(name):\n    s = epa_rows.Source.repository()\n"
                    "    return epa_rows._load_json(os.path.join(s.engine_dir, name, 'epa_engine.json'))\n",
             "epa_fit.py", "test_epa_rows.py"),
            # the third isolation review's planted leaks (24 October 2026, its scratch iso_leaks_test.py), each of
            # which gave no hit before N13 and N12's widening to epa_freeze
            ("N13", LEAK_GIT_SRC, "epa_fit.py", None),
            ("N13", LEAK_CHILD_SRC, "epa_stats.py", None),
            ("N12", LEAK_FREEZE_PRIVATE_SRC, "calibrate_epa.py", "test_epa_freeze.py"),
            ("N12", "import epa_freeze\nepa_freeze._read_json('x')\n", "validate_epa.py", "epa_freeze.py"),
            ("N12", "from epa_freeze import _git_ok\n", "epa_stats.py", "test_epa_freeze.py"),
            ("N12", "import epa_freeze\ngetattr(epa_freeze, '_' + 'git')\n", "epa_fit.py", "test_epa_freeze.py"),
            ("N13", "import subprocess\n", "epa_fit.py", "epa_freeze.py"),
            ("N13", "import epa_freeze\ndef s(root):\n    return epa_freeze.subprocess.run(['git', 'show'], cwd=root)\n",
             "calibrate_epa.py", "validate_epa.py"),
            ("N13", "import multiprocessing\ndef stage():\n    return multiprocessing.get_context('spawn').Pool(2)\n",
             "epa_fit.py", None),
            ("N13", "import multiprocessing\n", "epa_stats.py", None),
            ("N13", "import ctypes\n", "k3_knee.py", "d3_rows.py"),
            ("N13", "import concurrent.futures\n", "epa_stats.py", None),
            ("N13", "import os\nos.system('x')\n", "epa_coefficients.py", "epa_freeze.py"),
            ("N13", "from os import startfile\n", "epa_stats.py", None),
            ("N13", "import os\ngetattr(os, 'sys' + 'tem')('x')\n", "calibrate_epa.py", None),
            ("N13", "getattr(__import__('built' + 'ins'), 'op' + 'en')('x')\n", "epa_fit.py", "validate_epa.py"),
        ]
        for rule, src, bad, good in cases:
            self.assertTrue(self.flagged(rule, src, bad), (rule, bad, src))
            if good:
                self.assertFalse(self.flagged(rule, src, good), (rule, good, src))
        # the allowed contexts the rules name, each shown not flagged
        self.assertFalse(self.flagged("N5", "from thresholds import split\ndef arm():\n    split.compute()\n",
                                      "validate_epa.py"))
        self.assertFalse(self.flagged("N5", "from thresholds import split\ndef _arm_structure():\n"
                                            "    split.compute()\n", "validate_epa.py"))
        self.assertFalse(self.flagged("N5", "from thresholds import split\nclass Structural:\n    def t(self):\n"
                                            "        split.load('a', 'b')\n", "test_epa_rows.py"))
        self.assertFalse(self.flagged("N4", "import epa_rows\nclass Structural:\n    def t(self):\n"
                                            "        epa_rows.Source.repository()\n", "test_epa_rows.py"))
        self.assertFalse(self.flagged("N3", "from thresholds import common\nx = common.sha_text(common.CONTRACT_JSON)\n",
                                      "epa_freeze.py"))
        self.assertFalse(self.flagged("N1", f'"""a docstring naming {DE}/<id>/"""\n', "epa_freeze.py"))
        # N13's one exception: epa_fit's own pool helper names multiprocessing (its workers run the audit's
        # initializer); the same lines in any other function of epa_fit are flagged above
        self.assertFalse(self.flagged("N13", "import multiprocessing\ndef _pool(jobs, initializer):\n"
                                             "    return multiprocessing.get_context('spawn').Pool(jobs)\n", "epa_fit.py"))
        self.assertTrue(scan_words("x = '" + TABLE_WORDS[0] + ".csv'\n", "epa_stats.py"))
        self.assertTrue(scan_words("# " + TABLE_WORDS[1] + "\n", "test_epa_stats.py"))
        self.assertFalse(scan_words("x = '" + TABLE_WORDS[0] + "'\n", "thresholds/split.py"))

    def test_the_scan_reads_the_files_that_exist(self):
        """The scan is not vacuous: the loader and this file are among the files it reads."""
        here = [rel for rel in STEP2_CODE + STEP2_TESTS if os.path.isfile(os.path.join(HERE, rel))]
        self.assertIn("epa_rows.py", here)
        self.assertIn("test_epa_rows.py", here)
        self.assertIn("test_epa_fixtures.py", here)


# ============================================================================ Columns
def epa_map_literal(name):
    """A module-level literal of epa_map.py, read as source (no step-2 file imports epa_map, C3)."""
    tree = ast.parse(read("epa_map.py"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


def column_problems(headers, converted, dropped):
    """Columns of the pinned headers in neither or both of the two sets."""
    cols = {c for h in headers.values() for c in h}
    return sorted((cols - set(converted) - set(dropped)) | (set(converted) & set(dropped)))


class Columns(F.Guarded):
    def test_every_pinned_column_is_converted_or_dropped_never_both(self):
        self.assertEqual(column_problems(R.HEADERS, R.FIELD_OF_COLUMN, R.DROPPED_COLUMNS), [])
        # the control: a column taken out of the converted set, or put in both, is found
        conv = dict(R.FIELD_OF_COLUMN)
        conv.pop("turbine_inlet_temp_c")
        self.assertEqual(column_problems(R.HEADERS, conv, R.DROPPED_COLUMNS), ["turbine_inlet_temp_c"])
        self.assertEqual(column_problems(R.HEADERS, R.FIELD_OF_COLUMN, set(R.DROPPED_COLUMNS) | {"bmep_bar"}),
                         ["bmep_bar"])

    def test_every_converted_column_becomes_a_row_field(self):
        fields_ = {f.name for f in dataclasses.fields(R.PointRow)}
        self.assertEqual({v for v in R.FIELD_OF_COLUMN.values()} - fields_, set())

    def test_the_pins_of_epa_map_are_its_literals(self):
        self.assertEqual(R.KEY_COLUMNS, epa_map_literal("KEY_COLUMNS"))
        self.assertEqual(R.KEY_COLUMNS_STEADY, epa_map_literal("KEY_COLUMNS_STEADY"))
        self.assertEqual(R.PROVENANCE, epa_map_literal("PROVENANCE"))
        self.assertEqual(R.FIRST_DATA_ROW, epa_map_literal("FIRST_DATA_ROW"))
        channels = set(epa_map_literal("CHANNELS").values()) | set(R.PROVENANCE)
        for key, h in R.HEADERS.items():
            self.assertEqual(set(h) - channels, set(), key)
            self.assertEqual(tuple(h[:len(R.PROVENANCE)]), R.PROVENANCE, key)
        self.assertEqual(R.REQUIRED_POINT, tuple(c for c in R.KEY_COLUMNS if c != "spark_timing_cad_btdc"))

    def test_the_tables_are_the_generators(self):
        for eng, spec in split.ENG.items():
            self.assertEqual([t.name for t in R.TABLES[eng]], list(spec["steady"]) + [spec["hli"], spec["hlf"]])
            self.assertEqual({(t.role, t.index) for t in R.TABLES[eng]}, {k[1:] for k in R.HEADERS if k[0] == eng})


if __name__ == "__main__":
    unittest.main(verbosity=2)
