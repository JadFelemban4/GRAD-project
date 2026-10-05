"""Read one evaluate.py result file, results/<prefix>_seed<N>.txt, as text.

Pure. It imports nothing outside the standard library, reads only the file it
is given and writes nothing. The results tab (app/results_data.py) builds an
evaluation section from what it returns; app/test_results.py checks its
medians against analyse_phase_d.parse, the reader the preregistered analyses
use, on every result file in the tree.

The layout is the one evaluate.main() writes, top to bottom:

    the header line          "<title> -- [scored on the '<protocol>' protocol, ]
                              <n> FIXED EPISODES, frozen <date>"
    "scenario: ..." and "trigger: ..."
    the plant fingerprint    fingerprint.format_block(live, BLOCK_TITLE): a title
                             line, one "  <field>  <value>" line per field, a
                             closing line of dashes
    the provenance lines     "!! ..." when a plant mismatch was forced, with its
                             indented lines; "note ..."; "model <dir>: ..."
    the policy table         a header, a line of dashes, one row per policy
                             (label, then median damage, IQR width, worst
                             episode, median fuel, hottest turbine), dashes
    the knock-term block     "WITHOUT THE KNOCK TERM", one line per policy;
                             only in files evaluate.py wrote after it gained it

A policy row is read as analyse_phase_d.parse reads it: the LAST FIVE
whitespace fields are the numbers, because the label carries the run
directory and a path may hold digits. Its role comes from the label's prefix,
"agent (blind)" tested before "agent".

A file that is not an evaluation result raises NotEvaluationFile with a
reason the page can name. A file that cannot be read at all raises what
reading it raised (OSError, UnicodeDecodeError): that is a different failure,
and the caller reports it as one.
"""
import re
from pathlib import Path

NAME_RE = re.compile(r"^(?P<prefix>[a-z][a-z0-9]*(?:_[a-z0-9]+)*)_seed(?P<seed>[0-9]+)\.txt$")
HEADER_RE = re.compile(
    r"^(?P<title>.+?) -- (?:scored on the '(?P<protocol>[^']+)' protocol, )?"
    r"(?P<n>[0-9]+) FIXED EPISODES, frozen (?P<frozen>.+)$")
BLOCK_TITLE = "PLANT FINGERPRINT (this run)"
# label prefix -> role; "agent (blind)" is tested before "agent"
ROLE_PREFIXES = (("agent (blind)", "blind"), ("agent", "sighted"),
                 ("baseline ECU", "baseline"), ("reactive", "reactive"),
                 ("current-grade", "current_grade"))
ROLES = ("baseline", "reactive", "current_grade", "sighted", "blind")

_TITLE_RE = re.compile(r"^--- (?P<title>.+?)(?: -+)?\s*$")
_BLOCK_LINE_RE = re.compile(r"^  (\S+)(?:\s+(.*?))?\s*$")
_TABLE_HEAD_RE = re.compile(r"^policy\s+damage med\s+IQR\s+worst\s+fuel med\s+peak C\s*$")
_ROW_RE = re.compile(r"^(?P<label>\S.*?)" + r"\s+(\S+)" * 5 + r"\s*$")
_THERMAL_HEAD = "WITHOUT THE KNOCK TERM"
_THERMAL_RE = re.compile(r"^\s{4}(?P<name>.+?)\s+thermal med\s+(?P<med>-?[\d.]+)"
                         r"\s+thermal cut\s+(?P<cut>-?[\d.]+) %$")
_MODEL_RE = re.compile(r"^model (?P<dir>.+?): (?P<text>.*)$")
_DT_RE = re.compile(r"trained at dt ([\d.]+), scored at dt ([\d.]+)")
_BUDGET_RE = re.compile(r"trained (\d+) steps of (\d+) requested")
_ZIP_RE = re.compile(r"zip sha ([0-9a-f]+)")
_AGENT_ROLES = ("sighted", "blind")
_BOM = chr(0xFEFF)          # a byte-order mark, written without an escape


class NotEvaluationFile(ValueError):
    """The text is not an evaluate.py result file.

    `.reason` is one of: "header" (line one is not an evaluate.py header),
    "no_fingerprint" (no plant fingerprint block of this run), "no_table" (no
    policy row could be read) or "duplicate_role" (two rows for one role, so
    which agent the file scored is ambiguous)."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def parse_name(filename: str) -> tuple[str, int] | None:
    """("phase_d", 0) for "phase_d_seed0.txt"; None for any other name.

    The whole string must match: a path, a trailing newline or an upper-case
    letter is not a result file's name."""
    m = NAME_RE.fullmatch(filename)
    return (m["prefix"], int(m["seed"])) if m else None


def normalise_dir(text: str) -> str:
    """A run directory as a relative POSIX path, compared as text.

    evaluate.py writes the path it was given, with this machine's separator:
    "runs_c4\\sighted_seed0" becomes "runs_c4/sighted_seed0". Leading "./",
    "." segments, doubled separators and a trailing separator are dropped;
    case is kept."""
    parts = text.strip().replace("\\", "/").split("/")
    kept = [p for i, p in enumerate(parts) if p != "." and (p or i == 0)]
    return "/".join(kept)


def parse_block_line(line: str) -> tuple[str, str] | None:
    """One field line of a fingerprint block, as (field, value text).

    "  plant_sha                b5a3069f32a83754" gives ("plant_sha",
    "b5a3069f32a83754"). An empty value, as format_block renders an empty
    list, gives "", with or without the trailing spaces. None for any other
    line: a title, a line of dashes, a line not indented by exactly two."""
    m = _BLOCK_LINE_RE.match(line)
    if m is None:
        return None
    return m.group(1), m.group(2) or ""


def _title_of(line):
    m = _TITLE_RE.match(line)
    return m["title"] if m else None


def _is_rule(line):
    s = line.strip()
    return len(s) >= 3 and set(s) == {"-"}


def parse_fingerprint_block(lines: list[str]) -> dict[str, str]:
    """The fields of the first fingerprint block in `lines`, in order.

    The block starts at the first "--- <title> ---..." line, whatever the
    title, and ends at the next line made only of dashes. The same function
    reads a result file's block and a live block rendered by
    fingerprint.format_block, so the two sides are compared as the same text.
    {} when there is no title line. A field that appears twice keeps its first
    value."""
    out, inside = {}, False
    for line in lines:
        if not inside:
            inside = _title_of(line) is not None
            continue
        if _is_rule(line):
            break
        kv = parse_block_line(line)
        if kv is not None and kv[0] not in out:
            out[kv[0]] = kv[1]
    return out


def protocol_from_fingerprint(fp: dict[str, str]) -> str | None:
    """The protocol a block's rendered scenario names.

    A "protocol=random-climb" token is the d2 protocol; a scenario with no
    protocol token is phase-d, as agent_catalog.protocol_of reads a
    meta.json; any other protocol token, or no scenario field, is None."""
    scenario = fp.get("scenario")
    if scenario is None:
        return None
    named = [t[len("protocol="):] for t in scenario.split() if t.startswith("protocol=")]
    if not named:
        return "phase-d"
    return "d2" if named == ["random-climb"] else None


def _role_of(label):
    """(role, the label text after the role's prefix), or (None, "")."""
    for prefix, role in ROLE_PREFIXES:
        if label == prefix or (label.startswith(prefix) and label[len(prefix)].isspace()):
            return role, label[len(prefix):].strip()
    return None, ""


def _policy_row(line):
    """(role, policy dict) for one table row, or None when the row names no
    known role or its last five fields are not numbers."""
    m = _ROW_RE.match(line)
    if m is None:
        return None
    role, rest = _role_of(m["label"])
    if role is None:
        return None
    try:
        median, iqr, worst, fuel, peak = (float(m.group(k)) for k in range(2, 7))
    except ValueError:
        return None
    path = normalise_dir(rest) if role in _AGENT_ROLES else ""
    return role, {"label": m["label"], "dir": path or None, "median": median,
                  "iqr": iqr, "worst": worst, "fuel": fuel, "peak": peak}


def _forced_lines(lines):
    """Every "!!" line, each followed by the indented lines right after it."""
    out, inside = [], False
    for line in lines:
        if line.startswith("!!"):
            out.append(line)
            inside = True
        elif inside and line[:1].isspace() and line.strip():
            out.append(line)
        else:
            inside = False
    return out


def _dt_notes(notes):
    out = []
    for note in notes:
        m = _DT_RE.search(note)
        if m is None:
            continue
        try:
            pair = {"train_dt": float(m.group(1)), "eval_dt": float(m.group(2))}
        except ValueError:
            continue
        if pair not in out:
            out.append(pair)
    return out


def _models(lines):
    out = []
    for line in lines:
        m = _MODEL_RE.match(line)
        if m is None:
            continue
        budget = _BUDGET_RE.search(m["text"])
        zip_sha = _ZIP_RE.search(m["text"])
        out.append({"dir": normalise_dir(m["dir"]), "text": m["text"],
                    "steps": int(budget.group(1)) if budget else None,
                    "requested": int(budget.group(2)) if budget else None,
                    "zip_sha": zip_sha.group(1) if zip_sha else None})
    return out


def _policies(lines):
    """The policy table's rows by role. Raises no_table or duplicate_role."""
    head = next((i for i, line in enumerate(lines) if _TABLE_HEAD_RE.match(line)), None)
    if head is None:
        raise NotEvaluationFile("no_table")
    i = head + 1
    if i < len(lines) and _is_rule(lines[i]):
        i += 1
    out = {}
    while i < len(lines) and not _is_rule(lines[i]):
        row = _policy_row(lines[i])
        if row is not None:
            if row[0] in out:
                raise NotEvaluationFile("duplicate_role")
            out[row[0]] = row[1]
        i += 1
    if not out:
        raise NotEvaluationFile("no_table")
    return out


def _thermal(lines):
    """The knock-term block by role, None when the file has no such block.
    Read from its heading to the next blank line; a line that does not parse
    is skipped. Raises duplicate_role as the table does."""
    head = next((i for i, line in enumerate(lines)
                 if line.strip().startswith(_THERMAL_HEAD)), None)
    if head is None:
        return None
    out = {}
    for line in lines[head + 1:]:
        if not line.strip():
            break
        m = _THERMAL_RE.match(line)
        if m is None:
            continue
        role, _ = _role_of(m["name"])
        if role is None:
            continue
        try:
            entry = {"median": float(m["med"]), "cut": float(m["cut"])}
        except ValueError:
            continue
        if role in out:
            raise NotEvaluationFile("duplicate_role")
        out[role] = entry
    return out


def parse_eval_text(text: str) -> dict:
    """Everything the results tab reads from one result file's text.

    Raises NotEvaluationFile("header") when line one is not an evaluate.py
    header, ("no_fingerprint") when no "--- PLANT FINGERPRINT (this run)"
    block exists, ("no_table") when no policy row can be read and
    ("duplicate_role") when a role has two rows. A leading byte-order mark is
    ignored, and so are the line endings."""
    if text.startswith(_BOM):
        text = text[1:]
    lines = [line.rstrip() for line in text.splitlines()]
    head = HEADER_RE.match(lines[0]) if lines else None
    if head is None:
        raise NotEvaluationFile("header")
    start = next((i for i, line in enumerate(lines) if _title_of(line) == BLOCK_TITLE), None)
    if start is None:
        raise NotEvaluationFile("no_fingerprint")
    notes = [line for line in lines if line.startswith("note ")]
    return {
        "title": head["title"],
        "protocol": head["protocol"],
        "n_episodes": int(head["n"]),
        "frozen": head["frozen"],
        "scenario_line": next((line for line in lines if line.startswith("scenario:")), None),
        "trigger_line": next((line for line in lines if line.startswith("trigger:")), None),
        "fingerprint": parse_fingerprint_block(lines[start:]),
        "forced": _forced_lines(lines),
        "notes": notes,
        "dt_notes": _dt_notes(notes),
        "models": _models(lines),
        "policies": _policies(lines),
        "thermal": _thermal(lines),
    }


def parse_eval_file(path) -> dict:
    """parse_eval_text of the file, read as UTF-8, with result["path"] = str(path)."""
    out = parse_eval_text(Path(path).read_text(encoding="utf-8"))
    out["path"] = str(path)
    return out
