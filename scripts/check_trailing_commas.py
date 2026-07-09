#!/usr/bin/env python
"""Enforce the project's source-layout conventions across .py / .md / .json / .graphql.

Four checks. The first three carry both ``--check`` (gate, exit 1) and ``--fix``
(auto-repair); the fourth (non-ASCII) is report-only in both modes:

1. **Trailing-comma layout** (``.py``) -- the explode-at-threshold rule below.
2. **Markdown link-definition scaffold** (``.md``) -- every markdown file must
   end with the canonical ``<!-- LINK DEFINITIONS -->`` block carrying all
   per-source category markers (``<!-- Root -->`` ... ``<!-- External -->``) in
   order, so the buckets are never silently dropped. The fixer rebuilds the
   footer, preserving every existing def line under its category and inserting
   any missing markers. Agent-instruction files (``EXEMPT_MD_SCAFFOLD_NAMES``:
   AGENTS.md / CLAUDE.md) are prose directives, not link-carrying docs, and are
   waived from this one check.
3. **JSON / GraphQL brace explosion** (``.json`` / ``.graphql`` / ``.gql`` files
   and ```` ```json ```` / ```` ```graphql ```` fenced blocks in markdown) --
   content is normalized to its canonical pretty-printed form so every ``{``
   opens a new line. JSON goes through ``json.dumps(indent=2)`` (every object
   brace explodes); GraphQL through graphql-core's ``print_ast`` (selection sets
   explode; argument input-objects stay inline per the GraphQL convention).
   Detection is parse-gated: bare ``{`` in Python/JS, f-string interpolation,
   and unparseable pseudo-snippets are never touched, and the fix output is
   itself canonical (fixpoint-safe). ``.py`` string literals are out of scope.
4. **ASCII-only source** (``.py``) -- the source must be ASCII apart from emoji
   (the kanban example's parity markers). Em-dashes, arrows, ellipses, math
   signs etc. drift in from editors/paste; replace them with ASCII (``--``,
   ``->``, ``...``) or, where a non-ASCII runtime value is genuinely needed, an
   explicit unicode escape (kept out of f-string ``{...}`` expressions, which
   reject escapes before Python 3.12). Report-only (no safe universal auto-fix);
   emoji and the emoji variation selector are allowed.

Collection literals (list / set / dict / parenthesized tuple) and ``def`` /
method signatures are kept exploded one-item-per-line **iff** they have at least
``threshold`` items; anything below the threshold is kept inline. The threshold
is **4** by default and **2** for any ``models.py`` file.

The fixer is bidirectional:

* **>= threshold, single-line, no trailing comma**  -> add the comma (explode).
* **< threshold, has a trailing comma, fits on one line**  -> remove the comma
  (collapse). Constructs that are below threshold but genuinely too long to fit
  keep their comma (``ruff format`` leaves them multi-line and ``COM812`` owns
  them), so the fixer reaches a fixpoint with ruff rather than ping-ponging.

This covers the gap ``COM812`` cannot: ``COM812`` only adds a trailing comma to a
construct already split across lines, so single-line layout is never enforced by
ruff alone.

Usage::

    python scripts/check_trailing_commas.py [paths...]            # auto-fix (default)
    python scripts/check_trailing_commas.py --fix [paths...]      # auto-fix (explicit)
    python scripts/check_trailing_commas.py --check [paths...]    # gate (CI); exit 1

``paths`` may be files or directories; with none, the whole repo is scanned.
``--fix`` edits the commas and then runs ``ruff format`` on the touched files so
the layout actually reflows. Trailing commas are never added after ``*args`` /
``**kwargs`` (SyntaxError) or to one-element tuples, comment-bearing constructs
are left alone, and every fixed file is re-parsed before writing.
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import shutil
import subprocess
import sys
import tokenize
from collections.abc import Iterator
from pathlib import Path


def _ruff_line_length() -> int:
    """Read ``[tool.ruff] line-length`` from pyproject.toml -- the single source of truth.

    The collapse fit check must use the same width the formatter wraps at, or the
    two disagree and constructs churn; reading it (rather than copying it) keeps
    them locked together. Note this is the formatter target, NOT the E501 grace.
    """
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:
        match = re.search(r"(?m)^line-length\s*=\s*(\d+)", text)
        if match is None:
            raise RuntimeError("line-length not found in pyproject.toml") from None
        return int(match.group(1))
    return tomllib.loads(text)["tool"]["ruff"]["line-length"]


DEFAULT_THRESHOLD = 4
MODELS_THRESHOLD = 2
LINE_LENGTH = _ruff_line_length()
ROOTS = (
    "django_strawberry_framework",
    "tests",
    "examples/fakeshop",
    "scripts",
)
EXCLUDE_DIRS = frozenset(
    {
        ".venv",
        ".git",
        "__pycache__",
        "migrations",
        "build",
        "dist",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "node_modules",
        "docs",  # regenerable artifacts (docs/shadow/*.py), not authored source
    },
)
# Transient scratch trees -- never enforced (no scaffold / JSON / GraphQL layout),
# at any depth and for every file type. These are working notes, not authored
# source, and are meant to be churned/deleted freely.
EXCLUDE_SCRATCH_DIRS = frozenset(
    {
        "review",
        "bug_hunt",
        "builder",
        "shadow",
        "dry",
        "worker-memory",
    },
)
# Transient file-name substrings (case-insensitive): any file whose name contains
# one of these is excluded anywhere in the tree, for every suffix.
EXCLUDE_NAME_SUBSTRINGS = ("worker", "feedback")
# Agent-instruction markdown files exempt from the LINK-DEFINITIONS scaffold: they
# are prose directives, not standing docs with cross-file links, so they carry no
# link-definition footer. (Before this list AGENTS.md passed only incidentally --
# its prose quotes every scaffold marker in order -- which was fragile.) These files
# are still scanned for the JSON/GraphQL fence rule; only the scaffold is waived.
EXEMPT_MD_SCAFFOLD_NAMES = frozenset({"AGENTS.md", "CLAUDE.md"})
_CLOSE_BYTES = (b")", b"]", b"}")
_SKIP_TOK = frozenset(
    {
        tokenize.NL,
        tokenize.COMMENT,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
    },
)

# A construct is (open_line, open_col, close_line, close_col, item_count, can_add),
# with 0-based line indices and character columns.
Construct = tuple[int, int, int, int, int, bool]


def threshold_for(path: Path) -> int:
    """The explode threshold for ``path`` (2 for ``models.py``, else 4)."""
    return MODELS_THRESHOLD if path.name == "models.py" else DEFAULT_THRESHOLD


def _line_starts(text: str) -> list[int]:
    """Absolute char offset of the start of each line."""
    starts: list[int] = []
    offset = 0
    for line in text.split("\n"):
        starts.append(offset)
        offset += len(line) + 1
    return starts


def _byte_to_char(bline: bytes, byte_col: int) -> int:
    """Convert an ``ast`` byte column on a line to a character column."""
    return len(bline[:byte_col].decode("utf-8"))


def _literal_constructs(text: str, blines: list[bytes]) -> Iterator[Construct]:
    """Yield every >=2-item list/set/dict/parenthesized-tuple literal."""
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Dict):
            count = len(node.keys)
        elif isinstance(node, (ast.List, ast.Set, ast.Tuple)):
            count = len(node.elts)
        else:
            continue
        if count < 2:  # 0/1-item collections are never touched (incl. 1-tuples)
            continue
        open_bytes = blines[node.lineno - 1]
        if (
            isinstance(node, ast.Tuple)
            and open_bytes[node.col_offset : node.col_offset + 1] != b"("
        ):
            continue  # bare tuple (``a, b, c`` / ``return a, b``) -- skip
        close_byte = node.end_col_offset - 1
        close_bytes = blines[node.end_lineno - 1]
        if (
            not (0 <= close_byte < len(close_bytes))
            or close_bytes[close_byte : close_byte + 1] not in _CLOSE_BYTES
        ):
            continue  # self-verify: bail unless the offset really is a closing bracket
        yield (
            node.lineno - 1,
            _byte_to_char(open_bytes, node.col_offset),
            node.end_lineno - 1,
            _byte_to_char(close_bytes, close_byte),
            count,
            True,
        )


def _tokenize_info(text: str) -> tuple[list[Construct], list[int]]:
    """Return (>=2-param def signatures, absolute offsets of comment tokens)."""
    starts = _line_starts(text)
    toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    comments = [starts[t.start[0] - 1] + t.start[1] for t in toks if t.type == tokenize.COMMENT]
    sigs: list[Construct] = []
    n = len(toks)
    i = 0
    while i < n:
        if toks[i].type == tokenize.NAME and toks[i].string == "def":
            j = i + 1
            while j < n and not (toks[j].type == tokenize.OP and toks[j].string == "("):
                if toks[j].type in (tokenize.NEWLINE, tokenize.NL):
                    break
                j += 1
            if j < n and toks[j].type == tokenize.OP and toks[j].string == "(":
                open_tok = toks[j]
                depth = 1
                expect_seg = True
                last_seg_star = False
                seg_content = False
                commas = 0
                separators = 0
                close_tok = None
                k = j + 1
                while k < n:
                    tk = toks[k]
                    if tk.type == tokenize.OP and tk.string in ("(", "[", "{"):
                        depth += 1
                        expect_seg = False
                    elif tk.type == tokenize.OP and tk.string in (")", "]", "}"):
                        depth -= 1
                        if depth == 0:
                            close_tok = tk
                            break
                        expect_seg = False
                    elif depth == 1 and tk.type == tokenize.OP and tk.string == ",":
                        commas += 1
                        expect_seg = True
                    elif tk.type in _SKIP_TOK:
                        pass
                    elif depth == 1 and expect_seg:
                        # A depth-1 segment starting with a bare ``/`` (positional-
                        # only marker) or bare ``*`` (keyword-only marker) is a
                        # separator, NOT a parameter -- counting it would inflate
                        # the param total and could explode a 1-arg method to the
                        # syntactically-wrong ``def m(self, /,)``. ``*args`` /
                        # ``**kwargs`` ARE parameters: a ``*`` followed by an
                        # identifier is ``*args`` (real), while a ``*`` followed by
                        # ``,`` / ``)`` is the bare keyword-only marker.
                        is_separator = tk.string == "/"
                        if tk.string == "*":
                            nxt = k + 1
                            while nxt < n and toks[nxt].type in _SKIP_TOK:
                                nxt += 1
                            is_separator = nxt >= n or toks[nxt].string in (",", ")")
                        if is_separator:
                            separators += 1
                        else:
                            last_seg_star = tk.type == tokenize.OP and tk.string in ("*", "**")
                            seg_content = True
                        expect_seg = False
                    k += 1
                if close_tok is not None and seg_content:
                    # ``expect_seg`` is True at the close only when the last
                    # depth-1 token was a comma -- i.e. a trailing comma, which
                    # must not be counted as an extra parameter. Bare ``/`` / ``*``
                    # separators occupy comma-delimited slots but are not params,
                    # so subtract them from the segment total.
                    params = (commas if expect_seg else commas + 1) - separators
                    if params >= 2:
                        sigs.append(
                            (
                                open_tok.start[0] - 1,
                                open_tok.start[1],
                                close_tok.start[0] - 1,
                                close_tok.start[1],
                                params,
                                not last_seg_star,  # cannot add a comma after *args/**kwargs
                            ),
                        )
                i = k + 1
                continue
        i += 1
    return sigs, comments


def _inline_len(
    lines: list[str],
    oli: int,
    ocol: int,
    cli: int,
    ccol: int,
) -> int:
    """Approximate the length of the construct rendered on a single line."""
    prefix = lines[oli][:ocol]
    suffix = lines[cli][ccol + 1 :]
    if oli == cli:
        body = lines[oli][ocol : ccol + 1]
    else:
        segments = [lines[oli][ocol:]]
        segments.extend(lines[li].strip() for li in range(oli + 1, cli))
        segments.append(lines[cli][: ccol + 1].strip())
        body = " ".join(s for s in segments if s)
    body = re.sub(r"\s+", " ", body)
    body = re.sub(r",\s*([)\]}])", r"\1", body)  # drop the trailing comma
    body = re.sub(r",\s*", ", ", body)  # normalize ", "
    body = re.sub(r"([(\[{])\s+", r"\1", body)  # no pad after an opener
    body = re.sub(r"\s+([)\]}])", r"\1", body)  # no pad before a closer
    body = re.sub(r"\s+,", ",", body)  # no space before a comma
    return len(prefix) + len(body) + len(suffix)


def _analyze(text: str, threshold: int) -> tuple[list[int], list[int], list[tuple[int, str]]]:
    """Return (insert offsets, delete offsets, violations) for ``text``."""
    blines = text.encode("utf-8").split(b"\n")
    lines = text.split("\n")
    starts = _line_starts(text)
    sigs, comments = _tokenize_info(text)
    constructs = list(_literal_constructs(text, blines)) + sigs

    inserts: list[int] = []
    deletes: list[int] = []
    violations: list[tuple[int, str]] = []
    for oli, ocol, cli, ccol, count, can_add in constructs:
        open_abs = starts[oli] + ocol
        close_abs = starts[cli] + ccol
        scan = close_abs - 1
        while scan >= 0 and text[scan] in " \t\r\n":
            scan -= 1
        has_comma = scan >= 0 and text[scan] == ","
        single_line = oli == cli

        if count >= threshold:
            if single_line and can_add and not has_comma:
                inserts.append(close_abs)
                violations.append((oli + 1, "explode"))
        elif has_comma:  # below threshold and currently exploded
            src = text[open_abs : close_abs + 1]
            if '"""' in src or "'''" in src:
                continue  # multi-line strings -- never collapse
            if any(open_abs < c < close_abs for c in comments):
                continue  # comment inside -- ruff keeps it multi-line
            # A nested magic trailing comma (a child >= threshold, a 1-tuple, or a
            # too-long child) keeps that child multi-line, so this construct cannot
            # collapse. Detect any trailing comma other than our own.
            #
            # Known false-positive (degraded, never wrong): this scans raw text,
            # so a single-line string literal that happens to contain ``,)`` /
            # ``,]`` / ``,}`` (e.g. ``"(a,)"``) reads as a nested trailing comma
            # and the construct is conservatively NOT collapsed. The triple-quote
            # guard above already excludes multi-line strings; tightening this to
            # ignore string contents would need tokenizing ``inner``, which is not
            # worth it for a missed collapse (the layout stays valid either way).
            inner = src[: scan - open_abs] + src[scan - open_abs + 1 :]
            if re.search(r",\s*[)\]}]", inner):
                continue
            if _inline_len(lines, oli, ocol, cli, ccol) <= LINE_LENGTH:
                deletes.append(scan)
                violations.append((oli + 1, "collapse"))
    return inserts, deletes, violations


def _apply(text: str, inserts: list[int], deletes: list[int]) -> str:
    """Apply comma inserts/deletes to ``text`` (right-to-left so offsets hold)."""
    edits = sorted(
        [(off, True) for off in inserts] + [(off, False) for off in deletes],
        reverse=True,
    )
    for off, is_insert in edits:
        text = text[:off] + "," + text[off:] if is_insert else text[:off] + text[off + 1 :]
    return text


def _run_ruff_format(files: list[Path]) -> None:
    """Reflow the touched files so added/removed commas take visual effect."""
    ruff = shutil.which("ruff")
    cmd = ([ruff] if ruff else ["uv", "run", "ruff"]) + ["format", *(str(f) for f in files)]
    try:
        result = subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print("note: ruff not found on PATH; run `uv run ruff format` to reflow", file=sys.stderr)
        return
    if result.returncode != 0:
        print(f"warning: `ruff format` exited {result.returncode}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Markdown link-definition footer scaffold.
#
# Every ``.md`` file must end with the canonical LINK-DEFINITIONS scaffold so
# the per-source category buckets are never silently dropped (a real
# regression: editors strip "unused" category comments and the next author
# has nowhere to slot a link def). The check requires all markers present in
# canonical order; the fixer rebuilds the footer, preserving every existing
# def line under its category and inserting any missing category markers.
# ---------------------------------------------------------------------------

LINK_DEF_HEADER = "<!-- LINK DEFINITIONS -->"
LINK_DEF_CATEGORIES = (
    "<!-- Root -->",
    "<!-- docs/ -->",
    "<!-- docs/SPECS/ -->",
    "<!-- docs/builder/ -->",
    "<!-- django_strawberry_framework/ -->",
    "<!-- tests/ -->",
    "<!-- examples/ -->",
    "<!-- scripts/ -->",
    "<!-- .venv/ -->",
    "<!-- External -->",
)
_SCAFFOLD_MARKERS = (LINK_DEF_HEADER, *LINK_DEF_CATEGORIES)


def _scaffold_in_canonical_order(text: str) -> bool:
    """True iff every scaffold marker appears, each after the previous one."""
    pos = 0
    for marker in _SCAFFOLD_MARKERS:
        idx = text.find(marker, pos)
        if idx < 0:
            return False
        pos = idx + len(marker)
    return True


def _parse_footer(text: str) -> tuple[str, dict[str, list[str]], list[str]]:
    """Split ``text`` at the LINK-DEFINITIONS header.

    Returns ``(body, {category: [def lines]}, orphan_def_lines)``. ``orphan``
    holds def lines that sat under the header but before the first recognized
    category. With no header the whole text is the body.
    """
    idx = text.find(LINK_DEF_HEADER)
    if idx < 0:
        return text, {}, []
    body = text[:idx]
    footer = text[idx + len(LINK_DEF_HEADER) :]
    cats: dict[str, list[str]] = {}
    orphan: list[str] = []
    current: str | None = None
    for line in footer.split("\n"):
        stripped = line.strip()
        if stripped in LINK_DEF_CATEGORIES:
            current = stripped
            cats.setdefault(current, [])
        elif stripped == "":
            continue  # blank separators are rebuilt deterministically
        elif current is None:
            orphan.append(line.rstrip())
        else:
            cats[current].append(line.rstrip())
    return body, cats, orphan


def _render_footer(cats: dict[str, list[str]], orphan: list[str]) -> str:
    """Render the canonical footer with existing def lines slotted per category."""
    parts = [LINK_DEF_HEADER, ""]
    parts.extend(orphan)
    if orphan:
        parts.append("")
    for cat in LINK_DEF_CATEGORIES:
        parts.append(cat)
        parts.extend(cats.get(cat, []))
        parts.append("")
    while parts and parts[-1] == "":
        parts.pop()
    return "\n".join(parts) + "\n"


def fix_markdown_scaffold(text: str) -> str:
    """Ensure ``text`` ends with the canonical footer, preserving existing defs."""
    body, cats, orphan = _parse_footer(text)
    return body.rstrip("\n") + "\n\n" + _render_footer(cats, orphan)


# ---------------------------------------------------------------------------
# JSON / GraphQL brace explosion: every `{` must be followed by a newline.
#
# The rule applies ONLY to genuine JSON / GraphQL content -- standalone
# ``.json`` / ``.graphql`` / ``.gql`` files and ```json / ```graphql fenced
# blocks in markdown. Detection never touches bare ``{`` in Python/JS/etc.
# Empty ``{}`` (optionally ``{ }``) is exempt. The fixer reformats through the
# canonical pretty-printers (``json.dumps(indent=2)`` / graphql-core
# ``print_ast``), which guarantees every ``{`` opens a new line.
# ---------------------------------------------------------------------------

_FENCE = re.compile(
    r"(?m)^([ \t]*)```(json|graphql|gql)[ \t]*\n(.*?\n)?([ \t]*)```[ \t]*$",
    re.DOTALL,
)


def _format_json(content: str) -> str | None:
    """Pretty-print JSON at 2-space indent, or None if ``content`` is not JSON."""
    try:
        import json

        obj = json.loads(content)
    except (ValueError, TypeError):
        return None
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _format_graphql(content: str) -> str | None:
    """Fully explode a GraphQL document: every brace/bracket opens its own line.

    Field arguments each break onto their own 2-space-indented line too. Leaf
    values (strings, ints, floats, bools, null, enums, variables) and any
    node kind not handled here fall back to graphql-core's inline printer, so
    escaping and exotic constructs stay correct. Returns ``None`` if ``content``
    does not parse as GraphQL or hits an unexpected node shape (-> not enforced,
    never mangled). Deterministic, so re-formatting its own output is a no-op
    (fixpoint-safe).
    """
    try:
        from graphql import parse, print_ast
    except ImportError:
        return None
    try:
        document = parse(content)
    except Exception:
        return None

    def pad(level: int) -> str:
        return "  " * level

    def value(node: object, level: int) -> str:
        if node.kind == "object_value":
            if not node.fields:
                return "{}"
            rows = [
                f"{pad(level + 1)}{f.name.value}: {value(f.value, level + 1)}" for f in node.fields
            ]
            return "{\n" + "\n".join(rows) + "\n" + pad(level) + "}"
        if node.kind == "list_value":
            if not node.values:
                return "[]"
            rows = [f"{pad(level + 1)}{value(v, level + 1)}" for v in node.values]
            return "[\n" + "\n".join(rows) + "\n" + pad(level) + "]"
        return print_ast(node)  # string / int / float / bool / null / enum / variable

    def directives(nodes: object) -> str:
        return "".join(f" {print_ast(d)}" for d in nodes)

    def arguments(nodes: object, level: int) -> str:
        rows = [f"{pad(level + 1)}{a.name.value}: {value(a.value, level + 1)}" for a in nodes]
        return "(\n" + "\n".join(rows) + "\n" + pad(level) + ")"

    def selection_set(node: object, level: int) -> str:
        rows = [selection(s, level + 1) for s in node.selections]
        return "{\n" + "\n".join(rows) + "\n" + pad(level) + "}"

    def selection(node: object, level: int) -> str:
        if node.kind == "field":
            text = pad(level) + (f"{node.alias.value}: " if node.alias else "") + node.name.value
            if node.arguments:
                text += arguments(node.arguments, level)
            text += directives(node.directives)
            if node.selection_set:
                text += " " + selection_set(node.selection_set, level)
            return text
        if node.kind == "fragment_spread":
            return f"{pad(level)}...{node.name.value}{directives(node.directives)}"
        if node.kind == "inline_fragment":
            cond = f" on {node.type_condition.name.value}" if node.type_condition else ""
            head = f"{pad(level)}...{cond}{directives(node.directives)}"
            return head + " " + selection_set(node.selection_set, level)
        return pad(level) + print_ast(node)

    def definition(node: object) -> str:
        if node.kind == "operation_definition":
            anonymous = (
                node.operation.value == "query"
                and node.name is None
                and not node.variable_definitions
                and not node.directives
            )
            if anonymous:
                return selection_set(node.selection_set, 0)
            head = node.operation.value + (f" {node.name.value}" if node.name else "")
            if node.variable_definitions:
                head += "(" + ", ".join(print_ast(v) for v in node.variable_definitions) + ")"
            return head + directives(node.directives) + " " + selection_set(node.selection_set, 0)
        if node.kind == "fragment_definition":
            head = f"fragment {node.name.value} on {node.type_condition.name.value}"
            return head + directives(node.directives) + " " + selection_set(node.selection_set, 0)
        return print_ast(node)  # type-system / unhandled defs -> graphql-core inline printer

    try:
        return "\n\n".join(definition(d) for d in document.definitions)
    except Exception:
        return None


def _reformat(content: str, kind: str) -> str | None:
    """Return the exploded canonical form of a JSON/GraphQL block."""
    return _format_json(content) if kind == "json" else _format_graphql(content)


def _noncanonical(content: str, kind: str) -> str | None:
    """Return the canonical form if ``content`` is non-canonical JSON/GraphQL, else None.

    ``None`` means "nothing enforceable here": no ``{`` at all, content that does
    not parse as ``kind`` (e.g. an illustrative pseudo-snippet), or content
    already canonical. The fix output is itself canonical, so re-checking after a
    fix always passes (fixpoint-safe). ``json.dumps(indent=2)`` opens every
    object brace onto its own line; graphql-core's printer explodes selection
    sets while keeping argument input-objects inline per the GraphQL convention.
    """
    if "{" not in content:
        return None
    canonical = _reformat(content.strip(), kind)
    if canonical is None or canonical == content.strip():
        return None
    return canonical


def _reindent(block: str, indent: str) -> str:
    """Prefix every non-empty line of ``block`` with ``indent``."""
    return "\n".join(indent + line if line else line for line in block.split("\n"))


def _dedent(block: str, indent: str) -> str:
    """Strip a leading ``indent`` from each line of ``block`` that carries it."""
    return "\n".join(
        line[len(indent) :] if line.startswith(indent) else line for line in block.split("\n")
    )


def process_json_graphql_file(text: str, kind: str, do_fix: bool) -> tuple[bool, str]:
    """Check/fix a whole ``.json`` / ``.graphql`` file. Returns (violation, new_text)."""
    canonical = _noncanonical(text, kind)
    if canonical is None:
        return False, text
    if not do_fix:
        return True, text
    trailing = "\n" if text.endswith("\n") else ""
    return True, canonical + trailing


def process_markdown_fences(text: str, do_fix: bool) -> tuple[list[int], str]:
    """Check/fix ```json / ```graphql fenced blocks. Returns (violation lines, new_text)."""
    violations: list[int] = []
    out: list[str] = []
    last = 0
    for m in _FENCE.finditer(text):
        indent, lang, body = m.group(1), m.group(2), m.group(3) or ""
        kind = "json" if lang == "json" else "graphql"
        inner = body[:-1] if body.endswith("\n") else body
        dedented = _dedent(inner, indent)
        canonical = _noncanonical(dedented, kind)
        if canonical is None:
            continue
        violations.append(text.count("\n", 0, m.start()) + 1)
        if do_fix:
            out.append(text[last : m.start()])
            out.append(f"{indent}```{lang}\n{_reindent(canonical, indent)}\n{indent}```")
            last = m.end()
    if do_fix and last:
        out.append(text[last:])
        return violations, "".join(out)
    return violations, text


def iter_files(paths: list[str], suffixes: tuple[str, ...]) -> Iterator[Path]:
    """Yield files with one of ``suffixes`` (given files/dirs, or the whole repo).

    ``EXCLUDE_DIRS`` always drops external/generated trees (``.venv``, caches,
    ``node_modules``, ``build``/``dist``). The ``docs`` exclusion only applies
    to ``.py`` (regenerable ``docs/shadow/*.py``); markdown anywhere under
    ``docs`` is in scope per the "every ``.md``" rule -- EXCEPT the transient
    scratch trees in ``EXCLUDE_SCRATCH_DIRS`` and any file whose name contains a
    substring in ``EXCLUDE_NAME_SUBSTRINGS`` (worker / feedback), which are never
    enforced for any file type.
    """
    roots: list[Path] = [Path(p) for p in paths] if paths else [Path()]
    seen: set[Path] = set()
    for root in roots:
        files = (
            sorted(p for suf in suffixes for p in root.rglob(f"*{suf}"))
            if root.is_dir()
            else [root]
        )
        for path in files:
            if path.suffix not in suffixes:
                continue
            excluded = set(EXCLUDE_DIRS)
            if path.suffix != ".py":
                excluded.discard("docs")  # markdown under docs/ stays in scope
            excluded |= EXCLUDE_SCRATCH_DIRS  # scratch trees, every file type
            if any(part in excluded for part in path.parts):
                continue
            name = path.name.lower()
            if any(sub in name for sub in EXCLUDE_NAME_SUBSTRINGS):  # worker/feedback scratch
                continue
            if path not in seen:
                seen.add(path)
                yield path


def _is_emoji(cp: int) -> bool:
    """Allow emoji + emoji presentation selectors; reject other non-ASCII.

    The only non-ASCII permitted in ``.py`` source: the kanban example's parity
    markers (U+1F353 STRAWBERRY, U+269B ATOM + U+FE0F). Em-dashes / arrows /
    ellipses / math signs are NOT emoji and must be ASCII.
    """
    return (
        # Bounded to the pictographic planes (Mahjong .. Symbols-and-Pictographs
        # Extended-A) so astral CJK / Private-Use / language-tag codepoints are
        # still flagged, while emoji (e.g. U+1F353 STRAWBERRY) pass.
        0x1F000 <= cp <= 0x1FAFF
        # Miscellaneous Symbols ONLY (e.g. U+269B ATOM). Deliberately excludes
        # Dingbats (U+2700-27BF), which carry arrows (U+27A1) and math signs
        # (U+2795-2797) that the docstring promises to reject.
        or 0x2600 <= cp <= 0x26FF
        or 0xFE00 <= cp <= 0xFE0F  # variation selectors (U+FE0F = emoji presentation)
    )


def non_ascii_violations(text: str) -> list[tuple[int, int, str]]:
    """Return ``(lineno, col, char)`` for each disallowed non-ASCII char in ``.py`` text."""
    hits: list[tuple[int, int, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for col, ch in enumerate(line, 1):
            if ord(ch) > 0x7F and not _is_emoji(ord(ch)):
                hits.append((lineno, col, ch))
    return hits


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: ``--fix`` (default) or ``--check`` (gate) over ``paths``."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="report violations and exit 1 (no edits)",
    )
    mode.add_argument("--fix", action="store_true", help="auto-fix (the default)")
    parser.add_argument("paths", nargs="*", help="files/dirs to process (default: whole repo)")
    args = parser.parse_args(argv)
    do_fix = not args.check
    suffixes = (
        ".py",
        ".md",
        ".json",
        ".graphql",
        ".gql",
    )
    files = list(iter_files(args.paths, suffixes))

    messages = {
        "explode": "explode (>= threshold, no trailing comma)",
        "collapse": "collapse (< threshold, over-exploded)",
        "md-scaffold": "carry the canonical LINK-DEFINITIONS footer scaffold (all category markers)",
        "brace-explode": "explode JSON/GraphQL `{` onto its own line",
    }
    violations = 0
    changed: list[Path] = []
    py_changed: list[Path] = []
    ascii_hits: list[tuple[Path, int, int, str]] = []  # non-ASCII in .py (report-only)

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{path}: read error ({exc}) -- skipped", file=sys.stderr)
            continue
        new = text
        found: list[tuple[int, str]] = []

        if path.suffix == ".py":
            # Lexical, parse-independent -- run BEFORE the comma analysis so a
            # file that fails to parse still has its non-ASCII flagged (the
            # ``continue`` below would otherwise let banned chars slip the gate).
            ascii_hits.extend(
                (
                    path,
                    ln,
                    col,
                    ch,
                )
                for ln, col, ch in non_ascii_violations(text)
            )
            try:
                inserts, deletes, comma_found = _analyze(text, threshold_for(path))
            except (SyntaxError, tokenize.TokenError) as exc:
                print(f"{path}: parse error ({exc}) -- skipped", file=sys.stderr)
                continue
            found.extend(comma_found)
            if do_fix and (inserts or deletes):
                candidate = _apply(new, inserts, deletes)
                try:
                    ast.parse(candidate)
                    new = candidate
                except SyntaxError as exc:  # safety net -- never write broken syntax
                    print(
                        f"{path}: comma fix would break syntax ({exc}) -- skipped",
                        file=sys.stderr,
                    )

        elif path.suffix == ".md":
            if path.name not in EXEMPT_MD_SCAFFOLD_NAMES and not _scaffold_in_canonical_order(new):
                found.append((new.count("\n") + 1, "md-scaffold"))
                if do_fix:
                    new = fix_markdown_scaffold(new)
            fence_lines, fenced = process_markdown_fences(new, do_fix)
            found.extend((ln, "brace-explode") for ln in fence_lines)
            if do_fix:
                new = fenced

        else:  # .json / .graphql / .gql
            kind = "json" if path.suffix == ".json" else "graphql"
            viol, jg_new = process_json_graphql_file(new, kind, do_fix)
            if viol:
                found.append((1, "brace-explode"))
                if do_fix:
                    new = jg_new

        if args.check:
            for lineno, kind in sorted(found):
                print(f"{path}:{lineno}: should {messages[kind]}")
                violations += 1
        elif new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(path)
            if path.suffix == ".py":
                py_changed.append(path)

    # Non-ASCII in .py is report-only (no safe universal auto-fix) and fails in
    # BOTH modes, so the pre-commit `--fix` run catches it too, not just CI.
    for p, ln, col, ch in ascii_hits:
        print(
            f"{p}:{ln}:{col}: non-ASCII U+{ord(ch):04X} {ch!r} not allowed in .py (ASCII + emoji only)",
        )

    if args.check:
        if violations or ascii_hits:
            if violations:
                print(f"\n{violations} layout violation(s); run with --fix to resolve")
            if ascii_hits:
                print(
                    f"{len(ascii_hits)} non-ASCII char(s) in .py; replace with ASCII (emoji allowed)",
                )
            return 1
        return 0

    if py_changed:
        _run_ruff_format(py_changed)
    print(f"Fixed {len(changed)} file(s).")
    if ascii_hits:
        print(
            f"{len(ascii_hits)} non-ASCII char(s) in .py need manual replacement (emoji allowed)",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
