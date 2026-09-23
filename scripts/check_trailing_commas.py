#!/usr/bin/env python
"""Enforce the project's source-layout conventions across .py / .md / .json / .graphql.

Four checks. The first three carry both ``--check`` (gate, exit 1) and ``--fix``
(auto-repair); the fourth (non-ASCII) is report-only in both modes:

1. **Trailing-comma layout** (``.py``) -- the explode-at-threshold rule below.
2. **Markdown link-definition scaffold** (``.md``) -- every markdown file must
   end with the canonical ``<!-- LINK DEFINITIONS -->`` block carrying all
   per-source category markers (``<!-- Root -->`` ... ``<!-- External -->``) in
   order, so the buckets are never silently dropped. The footer is the LAST
   header standing alone on its own line outside any fenced block: START.md and
   docs/SPECS/NEXT.md document this convention by quoting every marker in prose,
   and a first-occurrence anchor would let that prose pass for the footer it
   describes. The fixer rebuilds the block, preserving every existing def line
   under its category and inserting any missing markers. Agent-instruction files
   (``EXEMPT_MD_SCAFFOLD_NAMES``: AGENTS.md / CLAUDE.md) are prose directives,
   not link-carrying docs, and are waived from this one check.
3. **JSON / GraphQL brace explosion** (``.json`` / ``.graphql`` / ``.gql`` files
   and ```` ```json ```` / ```` ```graphql ```` fenced blocks in markdown) --
   content is normalized to its canonical pretty-printed form so every ``{``
   opens a new line. JSON goes through ``json.dumps(indent=2)`` (every object
   brace explodes); GraphQL through graphql-core's ``print_ast`` (selection sets
   explode; argument input-objects stay inline per the GraphQL convention).
   Detection is parse-gated: bare ``{`` in Python/JS, f-string interpolation,
   and unparseable pseudo-snippets are never touched, and the fix output is
   itself canonical (fixpoint-safe). ``.py`` string literals are out of scope,
   and so is anything nested inside a wider fence -- a ```` ```json ```` block
   quoted as an example inside a ````` ````text ````` block is content.
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
  The fit measurement is taken on the token stream, so whitespace inside a
  string literal counts toward the width exactly as the formatter counts it.

This covers the gap ``COM812`` cannot: ``COM812`` only adds a trailing comma to a
construct already split across lines, so single-line layout is never enforced by
ruff alone.

Usage::

    python scripts/check_trailing_commas.py [paths...]            # auto-fix (default)
    python scripts/check_trailing_commas.py --fix [paths...]      # auto-fix (explicit)
    python scripts/check_trailing_commas.py --check [paths...]    # gate (CI); exit 1
    python scripts/check_trailing_commas.py --diff [paths...]     # --check + the fix as a diff
    python scripts/check_trailing_commas.py --check --json [...]  # machine-readable result

``paths`` may be files or directories; with none, the whole repo is scanned.
A directory walk covers only what git would accept as content (tracked, plus
untracked and not ignored), so a sweep never reads -- or rewrites -- ``.claude/``
agent memory or any other ignored path; a file named explicitly on the command
line is still processed. Both modes report every violation they find, with the
file and line. ``--fix`` edits the commas and then runs ``ruff format`` on the
touched files so the layout actually reflows.

Every run ends with one summary line -- files checked, files excluded, files
ignored (unsupported suffix), violations, errors -- so a clean pass and a pass
over nothing never look alike. A named path that matches nothing, or a named
directory that yields no checkable file, is an error: a gate run over an empty
population is not a pass. A named file dropped by an exclusion is reported as
``excluded ... not checked``; a file an exclusion drops during a directory walk
is counted in the summary.

``--diff`` implies ``--check``: nothing is written, and the unified diff
``--fix`` would apply (``ruff format`` reflow included) is printed per file.
``--json`` replaces all human output with one JSON document on stdout:
``mode``, ``paths``, ``summary`` (``checked`` / ``excluded`` / ``ignored`` /
``violations`` / ``errors`` / ``fixed`` / ``exit``), the ``checked`` /
``excluded`` / ``ignored`` path lists, ``violations`` and ``errors`` as records
of ``file`` / ``line`` / ``rule`` / ``message`` / ``fixable``, and, with
``--diff``, ``diffs`` keyed by file. Rule ids are stable: ``explode``,
``collapse``, ``md-scaffold``, ``brace-explode``, ``non-ascii`` for violations;
``read-error``, ``parse-error``, ``unfixable``, ``unmatched-path`` for errors.

Exclusions are anchored to repo-relative paths (``EXCLUDE_PATTERNS``, built from
``EXCLUDE_SCRATCH_DIRS`` and ``EXCLUDE_SCRATCH_SUBTREES``): the per-cycle
artifacts of the docs/ agent flows and their scratch subtrees stay out, while
the standing docs beside them (``REVIEW.md``, ``BUILD.md``, ``worker-*.md``,
...) and tracked ``.py`` under ``docs/`` are checked. A directory of the same
name anywhere else in the tree is ordinary source.

What the fixer refuses to touch:

* One-element tuples and comment-bearing constructs (``ruff format`` keeps those
  multi-line regardless, so collapsing them would just churn).
* ``**kwargs`` signatures, by project convention (AGENTS.md). A trailing comma
  after ``*args`` OR ``**kwargs`` parses fine on every supported Python, and
  ``COM812`` adds both once a signature is multi-line; the bare ``*`` and ``/``
  markers are the genuine SyntaxError cases and are excluded from the parameter
  count instead.
* JSON that would not survive the round trip -- duplicate keys, ``NaN`` /
  ``Infinity``, or a float whose precision ``repr`` cannot restore.
* A markdown footer rebuild that would drop a line of the document.

Every fixed ``.py`` file is re-parsed before writing, a file's original line
endings are preserved, and a file that could not be read or parsed is reported
and counted -- it fails the gate rather than passing unexamined.
"""

from __future__ import annotations

import argparse
import ast
import decimal
import difflib
import functools
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tokenize
from bisect import bisect_left, bisect_right
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from fnmatch import fnmatch, fnmatchcase
from pathlib import Path
from types import MappingProxyType

REPO_ROOT = Path(__file__).resolve().parent.parent


@functools.cache
def line_length() -> int:
    """Read ``[tool.ruff] line-length`` from pyproject.toml -- the single source of truth.

    The collapse fit check must use the same width the formatter wraps at, or the
    two disagree and constructs churn; reading it (rather than copying it) keeps
    them locked together. Note this is the formatter target, NOT the E501 grace.

    Called lazily rather than at import: a module that reads a file at import time
    cannot be imported from outside the repo at all, which puts every function in
    here out of reach of a REPL or a test.
    """
    pyproject = REPO_ROOT / "pyproject.toml"
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"cannot read {pyproject}: {error}") from error
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:
        pass
    else:
        try:
            return int(tomllib.loads(text)["tool"]["ruff"]["line-length"])
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError(f"[tool.ruff] line-length missing from {pyproject}") from error
    # Scope the fallback to the [tool.ruff] table: a bare first-match regex would
    # happily read some other tool's line-length out of an earlier section.
    section = re.search(r"(?ms)^\[tool\.ruff\]\s*$(.*?)(?=^\[|\Z)", text)
    match = re.search(r"(?m)^line-length\s*=\s*(\d+)", section.group(1) if section else "")
    if match is None:
        raise RuntimeError(f"[tool.ruff] line-length missing from {pyproject}")
    return int(match.group(1))


DEFAULT_THRESHOLD = 4
MODELS_THRESHOLD = 2
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
    },
)
# Per-cycle artifacts of the docs/ agent flows, keyed by the ``docs/<name>/``
# subtree that holds them. Each glob matches a file name directly inside that
# subtree (``**`` = the whole subtree). These records close with their cycle and
# carry no link-definition scaffold by design; the standing docs beside them
# (``REVIEW.md``, ``BUILD.md``, ``ARTIFACT.md``, ``DRY.md``, ``HUNT.md``,
# ``worker-*.md``, ``dicta.md``) are authored source and stay in scope.
EXCLUDE_SCRATCH_DIRS = MappingProxyType(
    {
        "review": ("rev-*.md", "review-*.md"),
        "dry": ("dry-*.md",),
        "builder": ("bld-*.md", "build-*.md", "DONE/**"),
        "bug_hunt": ("bug_hunt-*.md",),
        "shadow": ("**",),
    },
)
# Untracked scratch subtrees any docs/ flow keeps beside its artifacts.
EXCLUDE_SCRATCH_SUBTREES = ("temp-tests", "worker-memory")
# Repo-relative, ``/``-segmented patterns: ``*`` matches within one segment and a
# whole-segment ``**`` matches any number of segments. Anchoring at the repo root
# is load-bearing: a basename rule (``review``, ``builder``, ``dry``) would drop a
# future ``django_strawberry_framework/builder/`` or ``tests/review/`` from every
# check with no output at all.
EXCLUDE_PATTERNS: tuple[str, ...] = (
    *(f"docs/{name}/{glob}" for name, globs in EXCLUDE_SCRATCH_DIRS.items() for glob in globs),
    *(f"docs/*/{name}/**" for name in EXCLUDE_SCRATCH_SUBTREES),
)
# Maintainer review inputs under ``docs/``, matched as anchored name globs and
# only there. As a bare substring the same rule would drop a future
# ``django_strawberry_framework/feedback.py`` from the gate with no output at all
# -- staged, matched by pre-commit, then silently unenforced.
EXCLUDE_DOC_NAME_GLOBS = ("feedback*.md",)
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


def _tokenize_info(text: str, starts: list[int]) -> tuple[list[Construct], list[int]]:
    """Return (>=2-param def signatures, absolute offsets of comment tokens)."""
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
                last_seg_kwargs = False
                seg_content = False
                commas = 0
                separators = 0
                close_tok = None
                # A ``lambda`` default carries its OWN comma-separated parameter
                # list at this same depth (``def f(a=lambda x, y: x, b=2)``);
                # counting those commas inflates the signature's parameter total
                # and can explode a below-threshold def. The list ends at the
                # lambda's ``:``.
                in_lambda = False
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
                    elif depth == 1 and tk.type == tokenize.NAME and tk.string == "lambda":
                        in_lambda = True
                        seg_content = True
                        expect_seg = False
                    elif depth == 1 and in_lambda and tk.type == tokenize.OP and tk.string == ":":
                        in_lambda = False
                    elif depth == 1 and in_lambda:
                        pass  # inside the lambda's own parameter list
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
                            # ``*args`` accepts a trailing comma; ``**kwargs`` is
                            # held exempt by project convention (AGENTS.md), so
                            # only the double star blocks the explode.
                            last_seg_kwargs = tk.type == tokenize.OP and tk.string == "**"
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
                                not last_seg_kwargs,  # **kwargs signatures stay exempt
                            ),
                        )
                i = k + 1
                continue
        i += 1
    return sigs, comments


_OPENERS = ("(", "[", "{")
_CLOSERS = (")", "]", "}")
_LAYOUT_SKIP = frozenset(
    {
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.COMMENT,
        tokenize.ENDMARKER,
    },
)


def _significant_tokens(body: str) -> list[tokenize.TokenInfo] | None:
    """Tokenize a bracketed construct, dropping layout-only tokens.

    ``None`` when the fragment does not tokenize on its own, which is the signal
    to fall back to a conservative measurement rather than guess.
    """
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(body).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return None
    return [t for t in toks if t.type not in _LAYOUT_SKIP]


def _rendered_len(body: str) -> int:
    """Length of a bracketed construct rendered on one line, string-literal safe.

    Whitespace is normalized between tokens, never inside them: collapsing runs of
    spaces with a regex over raw source shortens ``"a          b"`` along with the
    layout, which under-measures the construct, drops a comma the formatter then
    puts back, and leaves the file churning on every commit.
    """
    toks = _significant_tokens(body)
    if toks is None:
        return len(body)
    parts: list[str] = []
    previous: tokenize.TokenInfo | None = None
    for position, token in enumerate(toks):
        text = token.string
        if not text:
            continue
        if text == "," and _next_string(toks, position) in _CLOSERS:
            continue  # the trailing comma disappears when the construct collapses
        if previous is not None:
            spaced = token.start != previous.end
            if previous.string in _OPENERS or text in _CLOSERS or text == ",":
                spaced = False
            elif previous.string == ",":
                spaced = True
            if spaced:
                parts.append(" ")
        parts.append(text)
        previous = token
    return len("".join(parts))


def _next_string(toks: list[tokenize.TokenInfo], position: int) -> str:
    """The string of the next significant token after ``position`` (``""`` at end)."""
    nxt = position + 1
    return toks[nxt].string if nxt < len(toks) else ""


def _has_nested_trailing_comma(body: str) -> bool:
    """True when a child construct carries its own magic trailing comma.

    A nested trailing comma pins that child multi-line, so the parent cannot
    collapse. Detected on the token stream rather than by matching ``,)`` in raw
    text, which also fires on the CONTENTS of a string literal such as ``"(a,)"``.
    """
    toks = _significant_tokens(body)
    if toks is None:
        return True  # cannot prove it is safe to collapse
    depth = 0
    for position, token in enumerate(toks):
        if token.string in _OPENERS:
            depth += 1
        elif token.string in _CLOSERS:
            depth -= 1
        elif token.string == "," and depth >= 2 and _next_string(toks, position) in _CLOSERS:
            return True
    return False


def _inline_len(
    lines: list[str],
    oli: int,
    ocol: int,
    cli: int,
    ccol: int,
) -> int:
    """Length of the construct plus its line context, rendered on a single line."""
    prefix = lines[oli][:ocol]
    suffix = lines[cli][ccol + 1 :]
    if oli == cli:
        body = lines[oli][ocol : ccol + 1]
    else:
        body = "\n".join([lines[oli][ocol:], *lines[oli + 1 : cli], lines[cli][: ccol + 1]])
    return len(prefix) + _rendered_len(body) + len(suffix)


def _analyze(text: str, threshold: int) -> tuple[list[int], list[int], list[tuple[int, str]]]:
    """Return (insert offsets, delete offsets, violations) for ``text``."""
    blines = text.encode("utf-8").split(b"\n")
    lines = text.split("\n")
    starts = _line_starts(text)
    sigs, comments = _tokenize_info(text, starts)
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
            # Comment offsets arrive sorted, so the containment test is a pair
            # of binary searches, not a scan of every comment per construct.
            if bisect_left(comments, close_abs) - bisect_right(comments, open_abs) > 0:
                continue  # comment inside -- ruff keeps it multi-line
            # A nested magic trailing comma (a child >= threshold, a 1-tuple, or a
            # too-long child) keeps that child multi-line, so this construct cannot
            # collapse.
            if _has_nested_trailing_comma(src):
                continue
            if _inline_len(lines, oli, ocol, cli, ccol) <= line_length():
                deletes.append(scan)
                violations.append((oli + 1, "collapse"))
    return inserts, deletes, violations


def _apply(text: str, inserts: list[int], deletes: list[int]) -> str:
    """Apply comma inserts/deletes to ``text`` in one pass.

    Edits are collected left to right into segments and joined once; rewriting the
    whole string per edit copies the file as many times as it has violations.
    """
    edits = sorted([(off, True) for off in inserts] + [(off, False) for off in deletes])
    out: list[str] = []
    cursor = 0
    for off, is_insert in edits:
        out.append(text[cursor:off])
        if is_insert:
            out.append(",")
            cursor = off
        else:
            cursor = off + 1
    out.append(text[cursor:])
    return "".join(out)


def _run_ruff_format(files: list[Path], *, quiet: bool = False) -> None:
    """Reflow the touched files so added/removed commas take visual effect.

    ``quiet`` sends ruff's own report to stderr, keeping stdout for ``--json``.
    """
    ruff = shutil.which("ruff")
    cmd = ([ruff] if ruff else ["uv", "run", "ruff"]) + ["format", *(str(f) for f in files)]
    try:
        result = subprocess.run(cmd, check=False, capture_output=quiet, text=quiet)
    except FileNotFoundError:
        print("note: ruff not found on PATH; run `uv run ruff format` to reflow", file=sys.stderr)
        return
    if quiet and (result.stdout or result.stderr):
        print(f"{result.stdout}{result.stderr}".rstrip("\n"), file=sys.stderr)
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


_FENCE_LINE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
_FENCE_BARE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*$")


def _fenced_lines(lines: list[str]) -> list[bool]:
    """Flag each line that sits inside a fenced code block (fence lines included).

    A fence is closed only by a BARE run (no info string) of at least as many
    markers as opened it -- CommonMark's rule, and the same one
    ``iter_top_level_fences`` applies -- so a ```` ```json ```` line nested inside
    an outer ````` ````text ````` block (or inside a plain ```` ``` ```` block)
    stays content rather than closing or opening anything.
    """
    inside = [False] * len(lines)
    marker: str | None = None
    for index, line in enumerate(lines):
        if marker is None:
            match = _FENCE_LINE.match(line)
            if match is not None:
                marker = match.group(1)
                inside[index] = True
            continue
        inside[index] = True
        match = _FENCE_BARE.match(line)
        run = match.group(1) if match else None
        if run is not None and run[0] == marker[0] and len(run) >= len(marker):
            marker = None
    return inside


def _footer_line_index(lines: list[str]) -> int:
    """Index of the real LINK-DEFINITIONS header line, or ``-1``.

    The LAST header standing alone on its own line outside any fenced block. Both
    qualifiers are load-bearing: START.md and docs/SPECS/NEXT.md document this very
    convention, quoting the header and every category marker in canonical order in
    prose well above the footer they describe. Anchoring on the first occurrence
    let that prose satisfy the check on its own, and -- had the check ever failed --
    would have had the fixer treat the whole document from the prose down as a
    footer to rebuild.
    """
    fenced = _fenced_lines(lines)
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip() == LINK_DEF_HEADER and not fenced[index]:
            return index
    return -1


def _scaffold_in_canonical_order(text: str) -> str | None:
    """The first missing/out-of-order scaffold marker, or ``None`` when canonical."""
    lines = text.split("\n")
    start = _footer_line_index(lines)
    if start < 0:
        return LINK_DEF_HEADER
    cursor = start + 1
    for marker in LINK_DEF_CATEGORIES:
        while cursor < len(lines) and lines[cursor].strip() != marker:
            cursor += 1
        if cursor >= len(lines):
            return marker
        cursor += 1
    return None


def _parse_footer(text: str) -> tuple[str, dict[str, list[str]], list[str]]:
    """Split ``text`` at the LINK-DEFINITIONS header.

    Returns ``(body, {category: [def lines]}, orphan_def_lines)``. ``orphan``
    holds def lines that sat under the header but before the first recognized
    category. With no header the whole text is the body.
    """
    lines = text.split("\n")
    index = _footer_line_index(lines)
    if index < 0:
        return text, {}, []
    body = "\n".join(lines[:index])
    footer = "\n".join(lines[index + 1 :])
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


def _preserves_content(before: str, after: str) -> bool:
    """True when every non-blank line of ``before`` survives in ``after``.

    The scaffold fixer only ever adds category markers and re-sorts def lines under
    them, so a rewrite that DROPS a line has misread where the footer starts. This
    is the markdown counterpart of the ``ast.parse`` re-check that guards a comma
    fix: no rewrite is worth losing a line of a document to.
    """
    lost = Counter(line.strip() for line in before.split("\n") if line.strip())
    lost -= Counter(line.strip() for line in after.split("\n") if line.strip())
    return not lost


def fix_markdown_scaffold(text: str) -> str | None:
    """The canonical-footer form of ``text``, or ``None`` if that would lose content."""
    body, cats, orphan = _parse_footer(text)
    fixed = body.rstrip("\n") + "\n\n" + _render_footer(cats, orphan)
    return fixed if _preserves_content(text, fixed) else None


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

# Fenced blocks are found by scanning lines, not by one regex over the document.
# A regex cannot see nesting: `docs/builder/ARTIFACT.md` wraps a whole worked
# example in a four-backtick ````text block, and the ```json fences INSIDE it are
# illustrative content that must not be reformatted.
_FENCE_OPEN = re.compile(r"^([ \t]*)(`{3,}|~{3,})[ \t]*([A-Za-z0-9_+-]*)[ \t]*$")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build the object, refusing input where one key is given twice.

    ``json.loads`` keeps the last value silently, so a rewrite of such a file would
    DELETE a line the author wrote. Refusing the parse leaves the file untouched.
    """
    obj: dict[str, object] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate key {key!r}")
        obj[key] = value
    return obj


def _reject_constant(name: str) -> object:
    """Refuse ``NaN`` / ``Infinity`` / ``-Infinity``, which are not valid JSON."""
    raise ValueError(f"{name} is not valid JSON")


def _load_json(content: str, *, exact: bool = False) -> object:
    """Parse JSON, refusing the non-standard constructs this fixer must not rewrite."""
    return json.loads(
        content,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_constant,
        parse_float=decimal.Decimal if exact else float,
    )


_WARNED: set[str] = set()


def _warn_once(message: str) -> None:
    """Print ``message`` to stderr the first time it is raised in this run."""
    if message not in _WARNED:
        _WARNED.add(message)
        print(message, file=sys.stderr)


def _format_json(content: str) -> str | None:
    """Pretty-print JSON at 2-space indent, or None if ``content`` is not JSON."""
    try:
        canonical = json.dumps(_load_json(content), indent=2, ensure_ascii=False)
    except (ValueError, TypeError, RecursionError):
        return None
    # Re-read both forms with exact decimal arithmetic and refuse to rewrite unless
    # they agree. ``json.dumps`` renders a float through ``repr``, which turns
    # ``1.000000000000000000001`` into ``1.0`` and ``1e999`` into the invalid token
    # ``Infinity``; neither is a layout change, so neither is this fixer's to make.
    try:
        if _load_json(content, exact=True) != _load_json(canonical, exact=True):
            return None
    except (ValueError, TypeError, RecursionError):
        return None
    return canonical


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
        from graphql import GraphQLError, parse, print_ast
    except ImportError:
        _warn_once(
            "note: graphql-core is not installed; the GraphQL layout rule is not "
            "enforced this run (it arrives with strawberry-graphql -- try `uv sync`)",
        )
        return None
    try:
        document = parse(content)
    except GraphQLError:
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
    except (
        AttributeError,
        TypeError,
        KeyError,
        RecursionError,
    ):
        return None  # an unexpected node shape -> not enforced, never mangled


def _reformat(content: str, kind: str) -> str | None:
    """Return the exploded canonical form of a JSON/GraphQL block."""
    return _format_json(content) if kind == "json" else _format_graphql(content)


def _noncanonical(content: str, kind: str) -> str | None:
    """Return the canonical form if ``content`` is non-canonical JSON/GraphQL, else None.

    ``None`` means "nothing enforceable here": content that does not parse as
    ``kind`` (e.g. an illustrative pseudo-snippet), GraphQL with no ``{`` at all,
    or content already canonical. The fix output is itself canonical, so re-checking after a
    fix always passes (fixpoint-safe). ``json.dumps(indent=2)`` opens every
    object brace onto its own line; graphql-core's printer explodes selection
    sets while keeping argument input-objects inline per the GraphQL convention.
    """
    if kind == "graphql" and "{" not in content:
        return None  # SDL-only fragments carry no selection set to explode
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


def _first_divergence(before: str, after: str) -> int:
    """1-based line number where ``after`` first differs from ``before``.

    A whole-file reformat has no single offending offset, but pointing at the first
    line that actually changes beats reporting every one of them against line 1.
    """
    old_lines, new_lines = before.split("\n"), after.split("\n")
    for index, (old_line, new_line) in enumerate(zip(old_lines, new_lines, strict=False), 1):
        if old_line != new_line:
            return index
    return min(len(old_lines), len(new_lines)) + 1


def process_json_graphql_file(text: str, kind: str) -> tuple[bool, str]:
    """Check a whole ``.json`` / ``.graphql`` file. Returns (violation, canonical text).

    The canonical form is returned in both modes so ``--check`` can report WHERE the
    file diverges; the caller decides whether to write it.
    """
    canonical = _noncanonical(text, kind)
    if canonical is None:
        return False, text
    trailing = "\n" if text.endswith("\n") else ""
    return True, canonical + trailing


def iter_top_level_fences(lines: list[str]) -> Iterator[tuple[int, int, str, str]]:
    """Yield ``(first body line, line after body, indent, language)`` per fence.

    Only top-level fences are yielded: an inner fence run shorter than the one that
    opened the block is body content. A fence left unclosed at end of file yields
    nothing, so an unterminated block is never half-rewritten.
    """
    index = 0
    total = len(lines)
    while index < total:
        match = _FENCE_OPEN.match(lines[index])
        if match is None:
            index += 1
            continue
        indent, marker, lang = match.group(1), match.group(2), match.group(3)
        close = index + 1
        while close < total:
            inner = _FENCE_OPEN.match(lines[close])
            if (
                inner is not None
                and not inner.group(3)
                and inner.group(2)[0] == marker[0]
                and len(inner.group(2)) >= len(marker)
            ):
                break
            close += 1
        if close >= total:
            return  # unterminated fence -- treat the rest of the file as content
        yield index + 1, close, indent, lang.lower()
        index = close + 1


def process_markdown_fences(text: str, do_fix: bool) -> tuple[list[int], str]:
    """Check/fix ```json / ```graphql fenced blocks. Returns (violation lines, new_text)."""
    lines = text.split("\n")
    violations: list[int] = []
    replacements: list[tuple[int, int, list[str]]] = []
    for start, end, indent, lang in iter_top_level_fences(lines):
        if lang not in ("json", "graphql", "gql"):
            continue
        kind = "json" if lang == "json" else "graphql"
        canonical = _noncanonical(_dedent("\n".join(lines[start:end]), indent), kind)
        if canonical is None:
            continue
        violations.append(start)  # the first body line, where the content actually is
        replacements.append((start, end, _reindent(canonical, indent).split("\n")))
    if not do_fix or not replacements:
        return violations, text
    out: list[str] = []
    cursor = 0
    for start, end, body in replacements:
        out.extend(lines[cursor:start])
        out.extend(body)
        cursor = end
    out.extend(lines[cursor:])
    return violations, "\n".join(out)


def _match_segments(pattern: tuple[str, ...], parts: tuple[str, ...]) -> bool:
    """Match ``parts`` against ``pattern`` segment by segment (``**`` = any run)."""
    if not pattern:
        return not parts
    head, rest = pattern[0], pattern[1:]
    if head == "**":
        return any(_match_segments(rest, parts[index:]) for index in range(len(parts) + 1))
    return bool(parts) and fnmatchcase(parts[0], head) and _match_segments(rest, parts[1:])


def matches_exclude_pattern(relative: str) -> bool:
    """True when the repo-relative posix path ``relative`` matches ``EXCLUDE_PATTERNS``.

    Matching is per segment, never over the joined string: ``fnmatch`` lets ``*``
    cross ``/``, which would make ``docs/review/rev-*.md`` swallow any file under a
    ``docs/review/rev-x/`` directory.
    """
    parts = tuple(relative.split("/"))
    return any(_match_segments(tuple(pattern.split("/")), parts) for pattern in EXCLUDE_PATTERNS)


def is_excluded(path: Path) -> bool:
    """True when ``path`` is outside the enforced set.

    ``EXCLUDE_DIRS`` always drops external/generated trees (``.venv``, caches,
    ``node_modules``, ``build``/``dist``, ``migrations``) at any depth. Inside the
    repo, ``EXCLUDE_PATTERNS`` drops the docs/ flows' per-cycle artifacts and
    scratch subtrees by repo-relative path, and ``EXCLUDE_DOC_NAME_GLOBS`` drops the
    maintainer inputs it names under a ``docs`` part. Everything else -- the
    standing docs beside the per-cycle ones and tracked ``.py`` under ``docs/``
    included -- is checked.
    """
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    relative = _repo_relative(path)
    if relative is not None and matches_exclude_pattern(relative):
        return True
    return "docs" in path.parts and any(
        fnmatch(path.name, glob) for glob in EXCLUDE_DOC_NAME_GLOBS
    )


@functools.cache
def git_visible_scope() -> tuple[frozenset[str], frozenset[str]] | None:
    """Repo-relative ``(files, directories)`` git would accept as content.

    ``--cached --others --exclude-standard`` is exactly "tracked, plus untracked
    but not ignored" -- the set of paths a commit can contain. Everything else on
    disk (``.claude/`` agent memory, local scratch, editor state) is ignored for a
    reason and is not this gate's to read, let alone rewrite.

    ``None`` when git cannot answer (not a checkout, git absent), which disables
    the filter rather than emptying the corpus: the tree-wide sweep must still
    work from an unpacked sdist.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except (OSError, ValueError):
        return None
    if result.returncode != 0:
        return None
    files = {path for path in result.stdout.split("\0") if path}
    if not files:
        return None
    directories: set[str] = set()
    for path in files:
        segments = path.split("/")[:-1]
        for depth in range(len(segments)):
            directories.add("/".join(segments[: depth + 1]))
    return frozenset(files), frozenset(directories)


def _repo_relative(path: Path) -> str | None:
    """``path`` as a repo-relative posix string, or ``None`` if it lies outside."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return None


def _walk(
    root: Path,
    suffixes: tuple[str, ...],
    excluded: list[Path] | None = None,
) -> Iterator[Path]:
    """Yield matching files under ``root``, pruning external directories in place.

    ``rglob`` would descend all of ``.venv`` and ``node_modules`` and discard the
    results afterwards; pruning at the directory level never visits them.

    Git-ignored paths are pruned too. A tree-wide run used to descend ``.claude/``
    and report a layout violation against an agent-memory file no commit can
    contain -- and under ``--fix`` it did not just report: it WROTE a
    LINK-DEFINITIONS footer into that file. An ignored path is not repo content,
    so the sweep does not read it. Paths named explicitly on the command line are
    still honoured; only the walk is filtered.

    A git-visible file with a checked suffix that an exclusion rule drops is
    appended to ``excluded`` (when given), so the run can count what it skipped.
    """
    scope = git_visible_scope()
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        relative = _repo_relative(here) if scope is not None else None
        base = "" if relative in (None, ".") else f"{relative}/"
        if scope is not None and relative is not None:
            visible = scope[1]
            dirnames[:] = [name for name in dirnames if f"{base}{name}" in visible]
        for name in sorted(filenames):
            path = here / name
            if path.suffix not in suffixes:
                continue
            if scope is not None and relative is not None and f"{base}{name}" not in scope[0]:
                continue
            if is_excluded(path):
                if excluded is not None:
                    excluded.append(path)
                continue
            yield path


@dataclass
class Selection:
    """What a run was handed and what it made of it.

    ``files`` are processed. ``skipped`` were named explicitly and dropped by an
    exclusion; ``excluded`` were reached by a directory walk and dropped by one;
    ``ignored`` were named explicitly with a suffix no rule covers; ``unmatched``
    pairs a named path with why it contributed nothing (missing, or a directory
    that yielded no checkable file).
    """

    files: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    excluded: list[Path] = field(default_factory=list)
    ignored: list[Path] = field(default_factory=list)
    unmatched: list[tuple[str, str]] = field(default_factory=list)


def select_files(paths: Sequence[str], suffixes: tuple[str, ...]) -> Selection:
    """Resolve ``paths`` (default: the repo root) into a ``Selection``.

    pre-commit passes staged paths, and its filters are looser than this script's,
    so it routinely hands over files that are dropped here. Returning them rather
    than swallowing them lets the caller say so: a silent skip reads exactly like a
    clean pass. The same holds for a path that names nothing and a directory whose
    walk comes back empty.
    """
    selection = Selection()
    seen: set[Path] = set()
    for raw in paths or ["."]:
        root = Path(raw)
        if root.is_dir():
            walked: list[Path] = []
            candidates = list(_walk(root, suffixes, walked))
            selection.excluded.extend(path for path in walked if path not in seen)
            seen.update(walked)
            if not candidates:
                selection.unmatched.append(
                    (raw, f"directory yielded no checkable file ({len(walked)} excluded)"),
                )
        elif not root.exists():
            selection.unmatched.append((raw, "matches nothing"))
            candidates = []
        elif root.suffix not in suffixes:
            if root not in seen:
                seen.add(root)
                selection.ignored.append(root)
            candidates = []
        elif is_excluded(root):
            if root not in seen:
                seen.add(root)
                selection.skipped.append(root)
            candidates = []
        else:
            candidates = [root]
        for path in candidates:
            if path not in seen:
                seen.add(path)
                selection.files.append(path)
    return selection


def iter_files(paths: Sequence[str], suffixes: tuple[str, ...]) -> tuple[list[Path], list[Path]]:
    """Return ``(files to process, explicitly-named files that were excluded)``.

    The two-list view of ``select_files``.
    """
    selection = select_files(paths, suffixes)
    return selection.files, selection.skipped


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
    r"""Return ``(lineno, col, char)`` for each disallowed non-ASCII char in ``.py`` text.

    Split on ``\n`` rather than with ``str.splitlines``, which also breaks on
    U+0085, U+2028 and U+2029 -- and CONSUMES them, so the very characters this
    check exists to surface never reach the loop, and every position after one is
    reported against the wrong line.
    """
    hits: list[tuple[int, int, str]] = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for col, ch in enumerate(line, 1):
            if ord(ch) > 0x7F and not _is_emoji(ord(ch)):
                hits.append((lineno, col, ch))
    return hits


def read_source(path: Path) -> tuple[str, str]:
    """Return ``(text with LF endings, the file's dominant line ending)``.

    Reading through ``utf-8-sig`` keeps a byte-order mark from reaching the parser
    (with it, ``ast.parse`` raises and the file is skipped -- unchecked but
    reported as fine), and normalizing CRLF in memory rather than at the codec
    keeps a one-comma fix from rewriting every line in the file.
    """
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        raw = handle.read()
    newline = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), newline


def write_source(path: Path, text: str, newline: str) -> None:
    """Write ``text`` back, restoring the file's original line ending."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", newline))


MESSAGES = {
    "explode": "explode (>= threshold, no trailing comma)",
    "collapse": "collapse (< threshold, over-exploded)",
    "md-scaffold": "carry the canonical LINK-DEFINITIONS footer scaffold (all category markers)",
    "brace-explode": "explode JSON/GraphQL `{` onto its own line",
}
SUFFIXES = (
    ".py",
    ".md",
    ".json",
    ".graphql",
    ".gql",
)


def _record(
    path: Path | str,
    line: int | None,
    rule: str,
    message: str,
    *,
    fixable: bool,
) -> dict[str, object]:
    """One violation or error record; every record carries the same keys."""
    return {
        "file": str(path),
        "line": line,
        "rule": rule,
        "message": message,
        "fixable": fixable,
    }


def _ruff_format_text(text: str, path: Path) -> str | None:
    """``text`` as ``ruff format`` would leave it at ``path``, or ``None`` if ruff failed.

    ``--stdin-filename`` makes ruff resolve the same configuration it applies to the
    file on disk, so a ``--diff`` shows the reflow ``--fix`` would produce.
    """
    ruff = shutil.which("ruff")
    cmd = ([ruff] if ruff else ["uv", "run", "ruff"]) + [
        "format",
        "--stdin-filename",
        str(path),
        "-",
    ]
    try:
        result = subprocess.run(cmd, input=text, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None
    return result.stdout if result.returncode == 0 else None


def _unified_diff(path: Path, before: str, after: str) -> str:
    """The unified diff turning ``before`` into ``after``, labelled with ``path``."""
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        ),
    )


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
    parser.add_argument(
        "--diff",
        action="store_true",
        help="with --check (implied): print the unified diff --fix would apply; writes nothing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print one JSON result document on stdout instead of human output",
    )
    parser.add_argument("paths", nargs="*", help="files/dirs to process (default: whole repo)")
    args = parser.parse_args(argv)
    if args.diff and args.fix:
        parser.error("--diff writes nothing; it cannot be combined with --fix")
    check = args.check or args.diff
    do_fix = not check

    def say(message: str = "", *, err: bool = False) -> None:
        if not args.json:
            print(message, file=sys.stderr if err else sys.stdout)

    selection = select_files(args.paths, SUFFIXES)
    files = selection.files
    for path in selection.skipped:
        say(f"{path}: excluded from the source-layout rules -- not checked", err=True)
    for path in selection.ignored:
        say(f"{path}: no source-layout rule covers this suffix -- ignored", err=True)
    records: list[dict[str, object]] = []
    error_records: list[dict[str, object]] = []
    for raw, reason in selection.unmatched:
        say(f"{raw}: {reason} -- NOT checked", err=True)
        error_records.append(_record(raw, None, "unmatched-path", reason, fixable=False))

    violations = 0
    errors = 0
    changed: list[Path] = []
    py_changed: list[Path] = []
    diffs: dict[str, str] = {}
    ascii_hits: list[tuple[Path, int, int, str]] = []  # non-ASCII in .py (report-only)

    for path in files:
        try:
            text, newline = read_source(path)
        except (OSError, UnicodeDecodeError) as exc:
            # A file that could not be read was not checked, so the run cannot
            # claim it passed: count it and fail, rather than printing and
            # exiting 0 on a file the gate never opened.
            say(f"{path}: read error ({exc}) -- NOT checked", err=True)
            error_records.append(_record(path, None, "read-error", str(exc), fixable=False))
            errors += 1
            continue
        new = text
        # (line, rule, fixable); the fixed text is computed in every mode so
        # ``--diff`` can show it and ``fixable`` is a fact, not a promise.
        found: list[tuple[int, str, bool]] = []
        scaffold_missing: str | None = None

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
                say(f"{path}: parse error ({exc}) -- NOT checked", err=True)
                error_records.append(_record(path, None, "parse-error", str(exc), fixable=False))
                errors += 1
                continue
            comma_fixable = True
            if inserts or deletes:
                candidate = _apply(new, inserts, deletes)
                try:
                    ast.parse(candidate)
                    new = candidate
                except SyntaxError as exc:  # safety net -- never write broken syntax
                    comma_fixable = False
                    if do_fix:
                        say(f"{path}: comma fix would break syntax ({exc}) -- skipped", err=True)
            found.extend((ln, kind, comma_fixable) for ln, kind in comma_found)

        elif path.suffix == ".md":
            scaffold_missing = (
                None
                if path.name in EXEMPT_MD_SCAFFOLD_NAMES
                else _scaffold_in_canonical_order(new)
            )
            if scaffold_missing is not None:
                rebuilt = fix_markdown_scaffold(new)
                found.append((new.count("\n") + 1, "md-scaffold", rebuilt is not None))
                if rebuilt is None:
                    if do_fix:
                        message = (
                            "rebuilding the LINK-DEFINITIONS footer would drop content "
                            "-- NOT fixed; repair the footer by hand"
                        )
                        say(f"{path}: {message}", err=True)
                        error_records.append(
                            _record(path, None, "unfixable", message, fixable=False),
                        )
                        errors += 1
                else:
                    new = rebuilt
            fence_lines, new = process_markdown_fences(new, True)
            found.extend((ln, "brace-explode", True) for ln in fence_lines)

        else:  # .json / .graphql / .gql
            kind = "json" if path.suffix == ".json" else "graphql"
            viol, jg_new = process_json_graphql_file(new, kind)
            if viol:
                found.append((_first_divergence(new, jg_new), "brace-explode", True))
                new = jg_new

        # Report what was found in BOTH modes. Under --fix these lines were being
        # computed and thrown away, so the run said only how many files it had
        # touched, never which rule fired or where.
        for lineno, kind, fixable in sorted(found):
            detail = MESSAGES[kind]
            if kind == "md-scaffold":
                detail = f"{detail} -- first missing marker: {scaffold_missing}"
            say(f"{path}:{lineno}: should {detail}")
            records.append(_record(path, lineno, kind, f"should {detail}", fixable=fixable))
            violations += 1
        if new == text:
            continue
        if do_fix:
            write_source(path, new, newline)
            changed.append(path)
            if path.suffix == ".py":
                py_changed.append(path)
        elif args.diff:
            after = new
            if path.suffix == ".py":
                reflowed = _ruff_format_text(new, path)
                if reflowed is None:
                    say(f"{path}: ruff format failed; diff shows the comma edits only", err=True)
                else:
                    after = reflowed
            diffs[str(path)] = _unified_diff(path, text, after)

    # Non-ASCII in .py is report-only (no safe universal auto-fix) and fails in
    # BOTH modes, so the pre-commit `--fix` run catches it too, not just CI.
    for hit_path, line, col, char in ascii_hits:
        message = f"non-ASCII U+{ord(char):04X} {char!r} not allowed in .py (ASCII + emoji only)"
        say(f"{hit_path}:{line}:{col}: {message}", err=True)
        records.append(
            _record(hit_path, line, "non-ascii", f"column {col}: {message}", fixable=False),
        )

    for diff in diffs.values():
        say(diff.rstrip("\n"))

    unmatched = len(selection.unmatched)
    if check:
        if violations:
            say(f"\n{violations} layout violation(s); run with --fix to resolve")
        if ascii_hits:
            say(f"{len(ascii_hits)} non-ASCII char(s) in .py; replace with ASCII (emoji allowed)")
        exit_code = 1 if (violations or ascii_hits or errors or unmatched) else 0
    else:
        if py_changed:
            _run_ruff_format(py_changed, quiet=args.json)
        say(f"Fixed {len(changed)} file(s).")
        if ascii_hits:
            say(
                f"{len(ascii_hits)} non-ASCII char(s) in .py need manual replacement "
                f"(emoji allowed)",
            )
        exit_code = 1 if (ascii_hits or errors or unmatched) else 0
    if errors:
        say(f"{errors} file(s) could not be checked")
    if unmatched:
        say(f"{unmatched} path(s) contributed no file to check")

    excluded_paths = [*selection.skipped, *selection.excluded]
    total_violations = violations + len(ascii_hits)
    say(
        f"source-layout: checked {len(files)} file(s); excluded {len(excluded_paths)}; "
        f"ignored {len(selection.ignored)}; violations {total_violations} "
        f"(layout {violations}, non-ASCII {len(ascii_hits)}); errors {errors + unmatched}",
    )
    if args.json:
        document = {
            "mode": "check" if check else "fix",
            "paths": list(args.paths),
            "summary": {
                "checked": len(files),
                "excluded": len(excluded_paths),
                "ignored": len(selection.ignored),
                "violations": total_violations,
                "errors": len(error_records),
                "fixed": len(changed),
                "exit": exit_code,
            },
            "checked": [str(path) for path in files],
            "excluded": [str(path) for path in excluded_paths],
            "ignored": [str(path) for path in selection.ignored],
            "violations": records,
            "errors": error_records,
        }
        if args.diff:
            document["diffs"] = diffs
        print(json.dumps(document, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
