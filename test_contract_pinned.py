"""test_contract_pinned.py -- the validation contract the EPA calibration runs under is version 5,
unchanged, and so are the code and the step outputs that wrote it (build step 2 of decision 24,
WP3; written 23 October 2026 against version 4 and repinned the same day to version 5, decision 77;
docs/build_step_2/PLAN.md 8.4, amendment C12, WP3_INTERFACES.md 9.2).

    python -B test_contract_pinned.py       a few seconds; exit code 0 when all pass

WHY IT EXISTS. `python engine_thresholds.py --check` rebuilt the contract in memory and compared
it with the two files. It can no longer pass, and must never be run: once calibrate_epa.py exists,
step 7's claim "calibrate_epa.py does not exist" refuses by design (thresholds/document.py), and a
run after any fit would write a new contract, which rule 0 forbids. This file checks the same thing
from the other end, without running a generator (PLAN.md 8.4; decision 66 dropped):

  ContractBlobs  both contract files' sha_text equal their blobs at VERSION_5, the commit that
                 committed version 5 (c842d74), no later commit touches either, and
                 epa_rows.CONTRACT_COMMIT names that commit; the JSON is schema 4 (version 5 kept
                 version 4's); once an EPA engine's freeze record exists, it names this contract
  Ancestry       VERSION_5 is an ancestor of HEAD, and of every commit that adds calibrate_epa.py
                 (git log --all), strictly: the contract binds from its first commit, "which must
                 precede calibrate_epa.py" (JSON `status`); and version 5's parent chain holds
                 VERSION_4 (a1b88e6), the version it was written on, whose blobs the files are not
  Generators     JSON generators.sha256 equal the generator files, and name exactly
                 engine_thresholds.GENERATORS (read from its source, never imported) and the files
                 of thresholds/
  StepOutputs    JSON generator_inputs_sha256 equal results/ENGINE_THRESHOLDS/*, name every step
                 output there but run.json, and `git diff --quiet -- results/ENGINE_THRESHOLDS/`
                 holds, with nothing untracked there either (amendment C12: the generators' writers
                 split.run, alpha_nodes.run, b58_propagation.run, ecu_shift.one and run_all and
                 common.printout write into that folder)
  Controls       each check run on a scratch input that breaks it, and caught (mistake 12): a
                 one-byte change in a copy of each contract file, of a generator and of a step
                 output; the files against version 4's blobs; a freeze record of another
                 contract; in a temporary repository, a commit of calibrate_epa.py that does
                 not descend from the contract and an edited or untracked step output; and an
                 unpinned generator or output

It reads the contract (WP3_INTERFACES.md 3.2 N3 allows this file to) and hashes the generators and
the step outputs, results/ENGINE_THRESHOLDS/split.json among them, as bytes: it parses none of them
but the contract, and prints no value. It opens nothing under data/ or logs/ (DataGuard). The
hashes are thresholds.common.sha_text's, the generators' own rule, and a blob at a commit is
epa_freeze.blob_sha256's (WP3_INTERFACES.md section 4).
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import epa_freeze  # noqa: E402
from thresholds import common  # noqa: E402

REPO = common.REPO
# VERSION 5 OF THE CONTRACT, PINNED HERE A SECOND TIME (epa_rows.CONTRACT_COMMIT is the first): the
# commit c842d74 "the validation contract, version 5: decision 77, the in-sample form criterion beyond
# sampling noise; the Run 1 go-ahead recorded". A change of either pin fails ContractBlobs, so the
# loader cannot move to another contract alone.
VERSION_5 = "c842d746ab8d50606dc5a3ae70c24bcc16f5f6c8"
# Version 4, the commit a1b88e6 "the validation contract, version 4: decision 39's rules, written before
# any fit", which WP3 was first pinned to: named for the history alone (Ancestry: version 5's parent chain
# holds it; Controls: the files are not its blobs), never as the contract held to.
VERSION_4 = "a1b88e62f9ad4e6cfe79a9ba6dd40887c55b5f45"
SCHEMA = 4
CONTRACT_FILES = (common.CONTRACT_JSON, common.CONTRACT_MD)
OUTPUTS = os.path.relpath(common.OUT_DIR, REPO).replace(os.sep, "/")       # results/ENGINE_THRESHOLDS
ENTRY = "engine_thresholds.py"
UNPINNED_OUTPUTS = ("run.json",)      # the steps' timings: the one file that holds a wall-clock time


def rel(path, root=REPO):
    return os.path.relpath(path, root).replace(os.sep, "/")


def contract():
    return common.load_json(common.CONTRACT_JSON)


def git(root, *args, check=True):
    out = subprocess.run(["git", "-c", "core.safecrlf=false", *args], cwd=root, capture_output=True, text=True,
                         env=dict(os.environ, **GIT_ENV))
    if check and out.returncode != 0:
        raise RuntimeError(f"git {args} in {root}: {out.stderr}")
    return out


GIT_ENV = {"GIT_AUTHOR_NAME": "wp3 test", "GIT_AUTHOR_EMAIL": "wp3@example.invalid",
           "GIT_COMMITTER_NAME": "wp3 test", "GIT_COMMITTER_EMAIL": "wp3@example.invalid",
           "GIT_AUTHOR_DATE": "2026-10-23T12:00:00+03:00", "GIT_COMMITTER_DATE": "2026-10-23T12:00:00+03:00"}


# ------------------------------------------------------------------ the checks, each a function of its inputs
def later_commits(root, since, files):
    """The commits after `since` up to HEAD in `root` that touch any of `files` (repository paths): the half of
    "no later commit touches the contract" that a working copy restored after the change would pass."""
    return git(root, "log", "--format=%H", f"{since}..HEAD", "--", *files).stdout.split()


def blob_mismatches(root, commit, pairs):
    """[repository path] of each (repository path, working file) whose working file's sha_text is
    not the blob that path has at `commit` in `root`."""
    return [r for r, working in pairs
            if not os.path.isfile(working) or common.sha_text(working) != epa_freeze.blob_sha256(commit, r, root=root)]


def hash_mismatches(pinned, base):
    """[name] of each {name: sha_text} entry whose file under `base` is missing or hashes otherwise."""
    out = []
    for name, want in pinned.items():
        p = os.path.join(base, *name.split("/"))
        if not os.path.isfile(p) or common.sha_text(p) != want:
            out.append(name)
    return out


def freeze_mismatches(record, json_path, md_path, commit):
    """The fields of a freeze record's `contract` block that do not name this contract."""
    want = {"commit": commit, "json_sha_text": common.sha_text(json_path), "md_sha_text": common.sha_text(md_path)}
    got = record.get("contract") or {}
    return sorted(k for k in want if got.get(k) != want[k]) + sorted(set(got) - set(want))


def adders(root, path):
    """Every commit, on any ref, that adds `path` (git log --all --diff-filter=A)."""
    out = git(root, "log", "--all", "--diff-filter=A", "--format=%H", "--", path).stdout.split()
    return sorted(set(out))


def not_after(root, commit, path):
    """The commits that add `path` and do not strictly descend from `commit`: each must have it as
    an ancestor and be another commit (the contract precedes calibrate_epa.py; JSON `status`)."""
    return [c for c in adders(root, path)
            if c == commit or not epa_freeze.is_ancestor(commit, c, root=root)]


def outputs_dirty(root, folder):
    """(git diff --quiet's exit code, the porcelain entries) for `folder` in `root`: 0 and [] when its
    tracked files are unchanged and nothing untracked sits there (amendment C12)."""
    quiet = git(root, "diff", "--quiet", "--", folder, check=False).returncode
    status = git(root, "status", "--porcelain", "--untracked-files=all", "--", folder).stdout.splitlines()
    return quiet, status


def generators_listed(entry_source):
    """engine_thresholds.GENERATORS, read from the entry point's source with ast: importing it is
    harmless, but this file runs no line of a generator."""
    tree = ast.parse(entry_source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "GENERATORS" for t in node.targets):
            return tuple(ast.literal_eval(node.value))
    raise AssertionError(f"{ENTRY} has no GENERATORS")


def package_files(root):
    """The files of thresholds/ that a commit would hold (tracked, or untracked and not ignored), and
    the entry point: what the generators' pin must name, every one."""
    out = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "--", "thresholds", ENTRY).stdout
    return sorted(set(out.split()))


def step_outputs(base):
    """Every step output under `base` the contract pins: each .json, recursively, but UNPINNED_OUTPUTS."""
    out = []
    for d, _dirs, files in os.walk(base):
        for f in files:
            if f.endswith(".json") and f not in UNPINNED_OUTPUTS:
                out.append(rel(os.path.join(d, f), base))
    return sorted(out)


def flip_one_byte(src, dst):
    """Copy `src` to `dst` with one byte changed: the first ASCII letter past the middle, its case
    flipped, so the change is one byte and never a line ending sha_text would fold."""
    with open(src, "rb") as fh:
        data = bytearray(fh.read())
    i = next(i for i in range(len(data) // 2, len(data)) if chr(data[i]).isascii() and chr(data[i]).isalpha())
    data[i] ^= 0x20
    with open(dst, "wb") as fh:
        fh.write(bytes(data))
    return i


# ------------------------------------------------------------------ the guard
class DataGuard:
    """An audit hook: while armed, an open of anything under the repository's data/ or logs/, or the
    team's data folder, is recorded (and fails the test in tearDown). This file reads the contract,
    the generators and the step outputs only."""
    armed = False
    seen = []
    roots = tuple(os.path.normcase(os.path.abspath(p)) for p in (
        os.path.join(REPO, "data"), os.path.join(REPO, "logs"), common.DATA_FOLDER))

    @classmethod
    def hook(cls, event, args):
        if cls.armed and event == "open" and args and not isinstance(args[0], int):
            try:
                p = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
            except (TypeError, ValueError):
                return
            if any(p == r or p.startswith(r + os.sep) for r in cls.roots):
                cls.seen.append(p)


sys.addaudithook(DataGuard.hook)


class Pinned(unittest.TestCase):
    def setUp(self):
        DataGuard.seen.clear()
        DataGuard.armed = True

    def tearDown(self):
        DataGuard.armed = False
        self.assertEqual(DataGuard.seen, [], "test_contract_pinned opened a file under data/ or logs/")


# ------------------------------------------------------------------ the tests
class ContractBlobs(Pinned):
    def test_both_contract_files_are_their_blobs_at_version_5(self):
        pairs = [(rel(p), p) for p in CONTRACT_FILES]
        self.assertEqual(blob_mismatches(REPO, VERSION_5, pairs), [])
        self.assertEqual(git(REPO, "cat-file", "-t", VERSION_5).stdout.strip(), "commit")

    def test_no_commit_after_version_5_touches_the_contract(self):
        """The working copy restored after a later commit changed the contract would pass the blob check above
        (WP3's fix of 23 October 2026, the test review's finding): HEAD's blobs equal VERSION_5's, and no commit
        between them touches either file. The controls: the comparison against VERSION_5's parent sees one; and
        later_commits, in a temporary repository, lists a later commit that touched a file and restored it, and not
        one that touched another file (WP3's third fix of 24 October 2026, on the test review's finding that the
        log half had no control)."""
        files = [rel(p) for p in CONTRACT_FILES]
        self.assertEqual(git(REPO, "diff", "--quiet", VERSION_5, "HEAD", "--", *files, check=False).returncode, 0)
        self.assertEqual(later_commits(REPO, VERSION_5, files), [])
        self.assertEqual(git(REPO, "diff", "--quiet", VERSION_5 + "~1", VERSION_5, "--", *files,
                             check=False).returncode, 1)
        with tempfile.TemporaryDirectory() as tmp:
            git(tmp, "init", "-q")
            f = os.path.join(tmp, "c.json")

            def commit(text, name="c.json", msg="x"):
                with open(os.path.join(tmp, name), "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                git(tmp, "add", "--", name)
                git(tmp, "commit", "-q", "-m", msg)
                return git(tmp, "rev-parse", "HEAD").stdout.strip()
            base = commit("{}\n")
            changed = commit("{\"a\": 1}\n", msg="a later change")
            restored = commit("{}\n", msg="restored")
            other = commit("x\n", name="other.txt", msg="another file")
            self.assertTrue(os.path.isfile(f))
            self.assertEqual(git(tmp, "diff", "--quiet", base, "HEAD", "--", "c.json", check=False).returncode, 0)
            self.assertEqual(sorted(later_commits(tmp, base, ["c.json"])), sorted([changed, restored]))
            self.assertNotIn(other, later_commits(tmp, base, ["c.json"]))
            self.assertEqual(later_commits(tmp, restored, ["c.json"]), [])

    def test_the_contract_is_schema_4_and_the_loader_pins_the_same_commit(self):
        """Version 5 kept schema 4 (its JSON's version_5.schema; the .md's section 14), so the loader's
        CONTRACT_SCHEMA is unchanged while its CONTRACT_COMMIT names version 5's commit."""
        self.assertEqual(contract()["schema"], SCHEMA)
        self.assertIn("version_5", contract(), "the working JSON carries version 5's record")
        try:
            import epa_rows
        except ModuleNotFoundError as e:
            if e.name != "epa_rows":
                raise
            self.skipTest("epa_rows.py is not written yet: its CONTRACT_COMMIT is checked once it is")
        self.assertEqual(epa_rows.CONTRACT_COMMIT, VERSION_5)
        self.assertEqual(epa_rows.CONTRACT_SCHEMA, SCHEMA)

    def test_each_freeze_record_names_this_contract(self):
        frozen = []
        for name in common.EPA_ENGINES:
            path = epa_freeze.freeze_path(name, root=REPO)
            if not os.path.exists(path):
                continue
            frozen.append(name)
            with self.subTest(engine=name):
                self.assertEqual(freeze_mismatches(common.load_json(path), *CONTRACT_FILES, VERSION_5), [])
        if not frozen:
            self.skipTest(f"no freeze record yet ({', '.join(common.EPA_ENGINES)}): each is checked once "
                          "calibrate_epa.py fit has written it (commit D)")


class Ancestry(Pinned):
    def test_version_5_is_an_ancestor_of_head(self):
        self.assertTrue(epa_freeze.is_ancestor(VERSION_5, "HEAD", root=REPO))

    def test_version_5_precedes_every_commit_that_adds_calibrate_epa(self):
        if not adders(REPO, "calibrate_epa.py"):
            self.skipTest("no commit adds calibrate_epa.py yet (commit C will, on a HEAD that descends from "
                          "version 5, which the test above checks)")
        self.assertEqual(not_after(REPO, VERSION_5, "calibrate_epa.py"), [])

    def test_version_5s_parent_chain_holds_version_4(self):
        """Version 5 was written on version 4 (its JSON's version_5.written: "on the tree of cfe6211 (version 4,
        a1b88e6, and its checkpoint)"): VERSION_4 is a strict ancestor of VERSION_5, so HEAD holds both. The
        control: VERSION_5 is no ancestor of VERSION_4."""
        self.assertEqual(git(REPO, "cat-file", "-t", VERSION_4).stdout.strip(), "commit")
        self.assertNotEqual(VERSION_4, VERSION_5)
        self.assertTrue(epa_freeze.is_ancestor(VERSION_4, VERSION_5, root=REPO))
        self.assertFalse(epa_freeze.is_ancestor(VERSION_5, VERSION_4, root=REPO))


class Generators(Pinned):
    def test_the_generator_files_are_the_pinned_ones(self):
        self.assertEqual(hash_mismatches(contract()["generators"]["sha256"], REPO), [])

    def test_every_generator_file_is_pinned(self):
        pinned = sorted(contract()["generators"]["sha256"])
        with open(os.path.join(REPO, ENTRY), encoding="utf-8") as fh:
            self.assertEqual(sorted(generators_listed(fh.read())), pinned)
        self.assertEqual(package_files(REPO), pinned)


class StepOutputs(Pinned):
    def test_the_step_outputs_are_the_pinned_ones(self):
        self.assertEqual(hash_mismatches(contract()["generator_inputs_sha256"], common.OUT_DIR), [])

    def test_every_step_output_is_pinned(self):
        self.assertEqual(step_outputs(common.OUT_DIR), sorted(contract()["generator_inputs_sha256"]))

    def test_git_sees_no_change_in_the_step_outputs(self):
        self.assertEqual(outputs_dirty(REPO, OUTPUTS), (0, []))


class Controls(Pinned):
    """Mistake 12: each check above, given an input that breaks it, says so."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        super().tearDown()

    def test_the_data_guard_records_an_open_under_data_and_logs(self):
        """The guard's own control (WP3's fourth fix of 24 October 2026, on the fourth tests review's finding that no
        test showed it records anything): an open of a path that does not exist under data/ and one under logs/ are
        recorded, then cleared; an open of a missing path elsewhere is not. Nothing is created."""
        for top in ("data", "logs"):
            with self.assertRaises(OSError):
                open(os.path.join(REPO, top, "__test_contract_pinned_no_such_file__"), "rb")
        with self.assertRaises(OSError):
            open(os.path.join(REPO, "results", "__test_contract_pinned_no_such_file__"), "rb")
        self.assertEqual(len(DataGuard.seen), 2, DataGuard.seen)
        DataGuard.seen.clear()

    def test_a_one_byte_change_to_either_contract_file_is_caught(self):
        for p in CONTRACT_FILES:
            with self.subTest(file=rel(p)):
                same = os.path.join(self.tmp, "same_" + os.path.basename(p))
                shutil.copyfile(p, same)
                self.assertEqual(blob_mismatches(REPO, VERSION_5, [(rel(p), same)]), [], "a faithful copy passes")
                bad = os.path.join(self.tmp, "flipped_" + os.path.basename(p))
                flip_one_byte(p, bad)
                self.assertEqual(blob_mismatches(REPO, VERSION_5, [(rel(p), bad)]), [rel(p)])
        # and the same files are not the blobs of version 4, the contract before version 5: both moved
        pairs = [(rel(p), p) for p in CONTRACT_FILES]
        self.assertEqual(blob_mismatches(REPO, VERSION_4, pairs), [rel(p) for p in CONTRACT_FILES])
        self.assertEqual(blob_mismatches(REPO, VERSION_5 + "~1", pairs), [rel(p) for p in CONTRACT_FILES])

    def test_a_one_byte_change_to_a_generator_or_a_step_output_is_caught(self):
        c = contract()
        for pinned, base, name in ((c["generators"]["sha256"], REPO, "thresholds/split.py"),
                                   (c["generator_inputs_sha256"], common.OUT_DIR, "b58_propagation.json")):
            with self.subTest(file=name):
                copy_base = os.path.join(self.tmp, name.replace("/", "_") + "_base")
                dst = os.path.join(copy_base, *name.split("/"))
                os.makedirs(os.path.dirname(dst))
                shutil.copyfile(os.path.join(base, *name.split("/")), dst)
                self.assertEqual(hash_mismatches({name: pinned[name]}, copy_base), [])
                flip_one_byte(os.path.join(base, *name.split("/")), dst)
                self.assertEqual(hash_mismatches({name: pinned[name]}, copy_base), [name])
                os.remove(dst)
                self.assertEqual(hash_mismatches({name: pinned[name]}, copy_base), [name], "a missing file is caught")

    def test_a_freeze_record_of_another_contract_is_caught(self):
        good = {"contract": {"commit": VERSION_5, "json_sha_text": common.sha_text(CONTRACT_FILES[0]),
                             "md_sha_text": common.sha_text(CONTRACT_FILES[1])}}
        self.assertEqual(freeze_mismatches(good, *CONTRACT_FILES, VERSION_5), [])
        bad_md = os.path.join(self.tmp, "md")
        flip_one_byte(CONTRACT_FILES[1], bad_md)
        self.assertEqual(freeze_mismatches(good, CONTRACT_FILES[0], bad_md, VERSION_5), ["md_sha_text"])
        older = {"contract": dict(good["contract"], commit="0" * 40)}
        self.assertEqual(freeze_mismatches(older, *CONTRACT_FILES, VERSION_5), ["commit"])
        v4 = {"contract": dict(good["contract"], commit=VERSION_4)}
        self.assertEqual(freeze_mismatches(v4, *CONTRACT_FILES, VERSION_5), ["commit"], "a record of version 4")
        self.assertEqual(freeze_mismatches({}, *CONTRACT_FILES, VERSION_5), ["commit", "json_sha_text", "md_sha_text"])

    def _repo(self):
        root = os.path.join(self.tmp, "repo")
        os.makedirs(root)
        git(root, "init", "-q", "-b", "main")
        return root

    def _commit(self, root, path, text, msg):
        p = os.path.join(root, *path.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        git(root, "add", "--", path)
        git(root, "commit", "-q", "-m", msg)
        return git(root, "rev-parse", "HEAD").stdout.strip()

    def test_a_calibration_commit_that_does_not_follow_the_contract_is_caught(self):
        root = self._repo()
        base = self._commit(root, "README", "base\n", "base")
        git(root, "checkout", "-q", "-b", "early")
        early = self._commit(root, "calibrate_epa.py", "# too early\n", "calibrate_epa.py before the contract")
        git(root, "checkout", "-q", "main")
        contract_commit = self._commit(root, "results/contract.json", "{}\n", "the contract")
        self.assertEqual(not_after(root, contract_commit, "calibrate_epa.py"), [early], "on another branch, caught")
        git(root, "branch", "-q", "-D", "early")
        self.assertEqual(not_after(root, contract_commit, "calibrate_epa.py"), [])
        late = self._commit(root, "calibrate_epa.py", "# after\n", "calibrate_epa.py after the contract")
        self.assertEqual(not_after(root, contract_commit, "calibrate_epa.py"), [])
        self.assertEqual(adders(root, "calibrate_epa.py"), [late])
        self.assertEqual(not_after(root, late, "calibrate_epa.py"), [late], "the same commit does not precede it")
        self.assertTrue(epa_freeze.is_ancestor(base, "HEAD", root=root))

    def test_an_edited_or_untracked_step_output_is_caught(self):
        root = self._repo()
        self._commit(root, "results/ENGINE_THRESHOLDS/split.json", "{\"a\": 1}\n", "a step output")
        self.assertEqual(outputs_dirty(root, "results/ENGINE_THRESHOLDS"), (0, []))
        p = os.path.join(root, "results", "ENGINE_THRESHOLDS", "split.json")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{\"a\": 2}\n")
        quiet, status = outputs_dirty(root, "results/ENGINE_THRESHOLDS")
        self.assertEqual((quiet, len(status)), (1, 1))
        git(root, "checkout", "--", "results/ENGINE_THRESHOLDS/split.json")
        self.assertEqual(outputs_dirty(root, "results/ENGINE_THRESHOLDS"), (0, []))
        with open(os.path.join(root, "results", "ENGINE_THRESHOLDS", "new.json"), "w") as fh:
            fh.write("{}\n")
        quiet, status = outputs_dirty(root, "results/ENGINE_THRESHOLDS")
        self.assertEqual(quiet, 0, "git diff alone does not see an untracked file")
        self.assertEqual(status, ["?? results/ENGINE_THRESHOLDS/new.json"], "the porcelain check does")

    def test_an_unpinned_generator_or_step_output_is_caught(self):
        base = os.path.join(self.tmp, "out")
        os.makedirs(os.path.join(base, "ecu"))
        for f in ("split.json", "run.json", "ecu/k3_nominal.json", "ecu/new.json", "split.txt"):
            with open(os.path.join(base, *f.split("/")), "w") as fh:
                fh.write("{}\n")
        self.assertEqual(step_outputs(base), ["ecu/k3_nominal.json", "ecu/new.json", "split.json"])
        self.assertNotEqual(step_outputs(base), sorted(["split.json", "ecu/k3_nominal.json"]))
        with open(os.path.join(REPO, ENTRY), encoding="utf-8") as fh:
            src = fh.read()
        listed = generators_listed(src)
        extra = src.replace('"thresholds/split.py",', '"thresholds/split.py", "thresholds/new.py",', 1)
        self.assertNotEqual(extra, src)
        self.assertEqual(sorted(generators_listed(extra)), sorted(listed + ("thresholds/new.py",)))
        self.assertNotEqual(sorted(generators_listed(extra)), sorted(contract()["generators"]["sha256"]))
        root = self._repo()
        self._commit(root, ENTRY, "GENERATORS = ()\n", "entry")
        self._commit(root, "thresholds/a.py", "\n", "a")
        with open(os.path.join(root, "thresholds", "b.py"), "w") as fh:
            fh.write("\n")
        self.assertEqual(package_files(root), [ENTRY, "thresholds/a.py", "thresholds/b.py"],
                         "an untracked generator file is listed, so an unpinned one is caught")


if __name__ == "__main__":
    unittest.main(verbosity=2)
