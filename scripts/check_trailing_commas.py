#!/usr/bin/env python
"""Enforce the project's explode-at-threshold trailing-comma layout (both ways).

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
            not (0 < close_byte <= len(close_bytes))
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
                        last_seg_star = tk.type == tokenize.OP and tk.string in ("*", "**")
                        seg_content = True
                        expect_seg = False
                    k += 1
                if close_tok is not None and seg_content:
                    # ``expect_seg`` is True at the close only when the last
                    # depth-1 token was a comma -- i.e. a trailing comma, which
                    # must not be counted as an extra parameter.
                    params = commas if expect_seg else commas + 1
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
        subprocess.run(cmd, check=False)  # noqa: S603
    except FileNotFoundError:
        print("note: ruff not found on PATH; run `uv run ruff format` to reflow", file=sys.stderr)


def iter_files(paths: list[str]) -> Iterator[Path]:
    """Yield the ``.py`` files to process (given files/dirs, or the whole repo)."""
    roots: list[Path] = [Path(p) for p in paths] if paths else [Path()]
    for root in roots:
        files = sorted(root.rglob("*.py")) if root.is_dir() else [root]
        for path in files:
            if path.suffix == ".py" and not any(part in EXCLUDE_DIRS for part in path.parts):
                yield path


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
    files = list(iter_files(args.paths))

    if args.check:
        violations = 0
        for path in files:
            try:
                _, _, found = _analyze(path.read_text(encoding="utf-8"), threshold_for(path))
            except (SyntaxError, tokenize.TokenError) as exc:
                print(f"{path}: parse error ({exc}) -- skipped", file=sys.stderr)
                continue
            for lineno, kind in found:
                action = (
                    "explode (>= threshold, no trailing comma)"
                    if kind == "explode"
                    else "collapse (< threshold, over-exploded)"
                )
                print(f"{path}:{lineno}: should {action}")
                violations += 1
        if violations:
            print(f"\n{violations} construct(s) violate the layout rule; run with --fix to resolve")
            return 1
        return 0

    changed: list[Path] = []
    edits = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
            inserts, deletes, _ = _analyze(text, threshold_for(path))
        except (SyntaxError, tokenize.TokenError) as exc:
            print(f"{path}: parse error ({exc}) -- skipped", file=sys.stderr)
            continue
        if not inserts and not deletes:
            continue
        new = _apply(text, inserts, deletes)
        try:
            ast.parse(new)
        except SyntaxError as exc:  # safety net -- never write broken syntax
            print(f"{path}: fix would break syntax ({exc}) -- skipped", file=sys.stderr)
            continue
        path.write_text(new, encoding="utf-8")
        changed.append(path)
        edits += len(inserts) + len(deletes)
    if changed:
        _run_ruff_format(changed)
    print(f"Adjusted {edits} trailing comma(s) across {len(changed)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
