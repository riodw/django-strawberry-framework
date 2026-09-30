"""Gate the package's public API at a 100% ``basedpyright --verifytypes`` score.

The package ships ``py.typed``, so every exported annotation is a contract a
consumer's type checker reads as written. ``mypy`` and ``basedpyright`` over the
package prove the code agrees with its declarations; neither proves the
declarations are complete. An exported name whose type a checker must infer
(and another checker may infer differently), a signature that mentions a type
this package leaves unknown, a public class or function without a docstring, or
a ``...`` default standing in for the real one is a hole only a consumer sees.
``basedpyright --verifytypes`` measures exactly that from a consumer's seat: it
reads the INSTALLED package, scores the share of exported symbols whose types
are known, and reports every symbol that falls short.

The gate passes only at a completeness score of exactly ``1.0`` with zero
diagnostics of any severity: per-symbol errors and warnings, and any general
diagnostic the run reports about the package as a whole. A report that lists no
symbol at all (the verifier found no package to measure, for instance no
``py.typed``) is never judged: it is a failed measurement, and its general
diagnostics are printed as the reason.

The one exception is ``ALLOWED_DIAGNOSTICS``: a diagnostic no declaration in this
package can clear without changing runtime behavior or lying to checkers. Each
entry is an exact ``(symbol, severity, message)`` paired with a one-line reason
that says why. A reported diagnostic is ignored only when it equals an entry in
all three fields, so a new diagnostic on an allowed symbol still fails. An entry
the verifier no longer reports fails the run as a stale allowlist entry, so an
entry cannot outlive its cause: once the cause is gone the entry is deleted.

How it measures:

* The package is installed NON-editable into a fresh environment inside a
  ``tempfile.TemporaryDirectory``, because ``--verifytypes`` does not follow an
  editable install and finds no ``py.typed`` through the shared ``.venv``.
  ``uv sync --frozen --no-editable --reinstall-package django-strawberry-framework
  --python <this interpreter>``, with ``UV_PROJECT_ENVIRONMENT`` naming that
  directory, installs the lock's default groups, so the soft dependencies and
  the stubs resolve for the verifier the way they do for the package checkers.
  ``--reinstall-package`` is load-bearing: uv caches the project's built wheel
  under a key read from ``pyproject.toml``, so without it a fresh environment
  can receive a build of older source.
* That environment's own ``basedpyright --verifytypes django_strawberry_framework
  --ignoreexternal --outputjson`` runs with the temporary directory as its
  working directory, outside the repository, and with ``VIRTUAL_ENV`` and
  ``PATH`` naming the environment: from inside the repository the project's
  configuration and source tree would be read instead of the installed package.
  ``--ignoreexternal`` discounts a type that is unknown inside another package;
  an unknown that surfaces in one of this package's own declarations still
  counts. ``--pythonversion`` is ``[tool.basedpyright] pythonVersion``, so the
  verifier reads the stubs at the Python the package checkers read them at,
  whichever interpreter runs the gate.
* Both children run without the caller's virtualenv, ``PYTHONPATH`` and ``uv``
  project redirects (``scripts/workspace.py`` strips the same family), so the
  measurement is the same from a shell, ``uv run``, pre-commit, CI and a
  workspace copy.

Usage::

    uv run python scripts/check_public_types.py

Exit code ``0`` when the score is ``1.0``, every reported diagnostic is an
allowlist entry and every allowlist entry is still reported; ``1`` when the score
falls short, any other diagnostic is reported, or an allowlist entry is stale;
``2`` when the measurement cannot run or measured nothing: ``uv`` or the
environment's ``basedpyright`` cannot be started, the environment build fails,
basedpyright prints no well-formed report, or the report lists no symbol.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "django_strawberry_framework"
DISTRIBUTION = "django-strawberry-framework"
#: The one passing score: every exported symbol's type is known.
PASSING_SCORE = 1.0
#: The symbol column for a diagnostic the run reports about the package as a whole.
GENERAL_SYMBOL = "<general>"
#: Variables that would point either child at another project, environment or
#: import path. ``UV_PROJECT_ENVIRONMENT`` and ``VIRTUAL_ENV`` are set again, to
#: the temporary environment, where a child needs them.
REDIRECTING_VARIABLES = frozenset(
    {
        "CONDA_PREFIX",
        "PYTHONHOME",
        "PYTHONPATH",
        "UV_FROZEN",
        "UV_LOCKED",
        "UV_NO_SYNC",
        "UV_PROJECT",
        "UV_PROJECT_ENVIRONMENT",
        "UV_WORKING_DIRECTORY",
        "VIRTUAL_ENV",
    },
)


class MeasurementError(RuntimeError):
    """The verifier could not produce a report to judge."""


class Diagnostic(NamedTuple):
    """One reported problem: the symbol it names, its severity, and its message."""

    symbol: str
    severity: str
    message: str


class AllowedDiagnostic(NamedTuple):
    """A diagnostic the gate accepts on an exact match, and why nothing here can clear it."""

    diagnostic: Diagnostic
    reason: str


#: Every diagnostic the gate accepts. Matched on all three fields; an entry the
#: verifier stops reporting is stale and fails the run.
ALLOWED_DIAGNOSTICS: tuple[AllowedDiagnostic, ...] = (
    AllowedDiagnostic(
        Diagnostic(
            "django_strawberry_framework.scalars.BigInt",
            "warning",
            'No docstring found for class "django_strawberry_framework.scalars.BigInt"',
        ),
        "pyright builds a NewType's class with no docstring slot, and the only fixes change "
        "runtime behavior or lie to checkers.",
    ),
    AllowedDiagnostic(
        Diagnostic(
            "django_strawberry_framework.filters.Filter",
            "warning",
            'No docstring found for class "django_strawberry_framework.filters.Filter"',
        ),
        "django-filter's own class, re-exported unchanged, ships without a docstring upstream.",
    ),
)


class Verdict(NamedTuple):
    """The gate's judgment of one report."""

    score: float
    #: Reported diagnostics no allowlist entry matches.
    failing: tuple[Diagnostic, ...]
    #: Allowlist entries a reported diagnostic matched.
    allowed: tuple[AllowedDiagnostic, ...]
    #: Allowlist entries no reported diagnostic matched.
    stale: tuple[AllowedDiagnostic, ...]

    @property
    def passing(self) -> bool:
        """A score of exactly ``1.0``, nothing unallowed reported, and no stale entry."""
        return self.score == PASSING_SCORE and not self.failing and not self.stale


def completeness_score(report: Mapping[str, object]) -> float:
    """Return the report's completeness score, or raise when it carries none."""
    completeness = report.get("typeCompleteness")
    if not isinstance(completeness, Mapping):
        raise MeasurementError("The basedpyright report carries no typeCompleteness section.")
    score = completeness.get("completenessScore")
    if isinstance(score, bool) or not isinstance(score, int | float):
        raise MeasurementError("The basedpyright report carries no numeric completenessScore.")
    return float(score)


def report_diagnostics(report: Mapping[str, object]) -> list[Diagnostic]:
    """Return every diagnostic in the report: the general ones first, then each symbol's."""
    diagnostics = [
        Diagnostic(GENERAL_SYMBOL, _text(entry, "severity"), _text(entry, "message"))
        for entry in _entries(report.get("generalDiagnostics"))
    ]
    for symbol in _symbol_entries(report):
        name = _text(symbol, "name")
        diagnostics.extend(
            Diagnostic(name, _text(entry, "severity"), _text(entry, "message"))
            for entry in _entries(symbol.get("diagnostics"))
        )
    return diagnostics


def _symbol_entries(report: Mapping[str, object]) -> list[Mapping[str, object]]:
    """The report's ``typeCompleteness.symbols`` entries, or none when it lists none."""
    completeness = report.get("typeCompleteness")
    return _entries(completeness.get("symbols") if isinstance(completeness, Mapping) else None)


def _entries(value: object) -> list[Mapping[str, object]]:
    """The mapping entries of a report list, or none when the key is absent."""
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(entry, Mapping) for entry in value):
        raise MeasurementError(f"Unexpected basedpyright report shape: {value!r:.200}")
    return value


def _text(entry: Mapping[str, object], key: str) -> str:
    """The string ``entry[key]``, or raise when the report entry carries none."""
    value = entry.get(key)
    if not isinstance(value, str):
        raise MeasurementError(
            f"A basedpyright report entry has no string {key!r}: {entry!r:.200}",
        )
    return value


def verdict_for(
    report: Mapping[str, object],
    allowlist: Sequence[AllowedDiagnostic] = ALLOWED_DIAGNOSTICS,
) -> Verdict:
    """Judge a parsed report, or raise when it lists no symbol to judge.

    A run that found no package reports a score over zero symbols; judging it
    would call every allowlist entry stale, so it is a failed measurement whose
    general diagnostics say why.
    """
    score = completeness_score(report)
    diagnostics = report_diagnostics(report)
    if not _symbol_entries(report):
        lines = [f"basedpyright measured no symbol of {PACKAGE} (score {score!r}):"]
        for diagnostic in diagnostics:
            lines.extend(_diagnostic_lines("", diagnostic))
        if not diagnostics:
            lines.append("  (no general diagnostic reported)")
        raise MeasurementError("\n".join(lines))
    return judge(score, diagnostics, allowlist)


def judge(
    score: float,
    diagnostics: Sequence[Diagnostic],
    allowlist: Sequence[AllowedDiagnostic] = ALLOWED_DIAGNOSTICS,
) -> Verdict:
    """Split ``diagnostics`` by ``allowlist`` into failing and allowed, and find stale entries."""
    allowed_diagnostics = {entry.diagnostic for entry in allowlist}
    reported = set(diagnostics)
    return Verdict(
        score=score,
        failing=tuple(item for item in diagnostics if item not in allowed_diagnostics),
        allowed=tuple(entry for entry in allowlist if entry.diagnostic in reported),
        stale=tuple(entry for entry in allowlist if entry.diagnostic not in reported),
    )


def _diagnostic_lines(prefix: str, diagnostic: Diagnostic) -> list[str]:
    """One diagnostic as output lines, its message addenda indented under the first."""
    message_lines = diagnostic.message.replace("\xa0", " ").splitlines() or [""]
    lines = [f"  {prefix}{diagnostic.severity}: {diagnostic.symbol}: {message_lines[0]}"]
    lines.extend(f"      {line.strip()}" for line in message_lines[1:])
    return lines


def format_report(verdict: Verdict) -> list[str]:
    """Render the score, every diagnostic and allowlist outcome, and the verdict as lines."""
    score = verdict.score
    lines = [f"verifytypes {PACKAGE}: completeness score {score:.4%} ({score!r})"]
    for diagnostic in verdict.failing:
        lines.extend(_diagnostic_lines("", diagnostic))
    for entry in verdict.allowed:
        lines.extend(_diagnostic_lines("allowed ", entry.diagnostic))
        lines.append(f"      reason: {entry.reason}")
    for entry in verdict.stale:
        lines.extend(_diagnostic_lines("stale allowlist entry: ", entry.diagnostic))
        lines.append("      the verifier no longer reports it; delete the entry.")
    if verdict.passing:
        lines.append(
            "OK: every exported symbol's type is known and nothing is reported beyond "
            f"{len(verdict.allowed)} allowlisted diagnostic(s).",
        )
    else:
        lines.append(
            f"FAIL: the gate needs a score of exactly {PASSING_SCORE:.0%}, no diagnostic "
            f"outside the allowlist and no stale allowlist entry; got {score:.4%}, "
            f"unallowed diagnostics: {len(verdict.failing)}, "
            f"stale allowlist entries: {len(verdict.stale)}.",
        )
    return lines


def parse_report(stdout: str) -> dict[str, object]:
    """Parse basedpyright's ``--outputjson`` stdout, or raise when it is not a report."""
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise MeasurementError(f"basedpyright printed no JSON report: {stdout[:500]!r}") from error
    if not isinstance(report, dict):
        raise MeasurementError(f"basedpyright printed a non-object report: {stdout[:500]!r}")
    return report


def child_environment(base: Mapping[str, str], **extra: str) -> dict[str, str]:
    """Return ``base`` without every redirecting variable, plus ``extra``."""
    env = {name: value for name, value in base.items() if name not in REDIRECTING_VARIABLES}
    env.update(extra)
    return env


def _uv_executable() -> str:
    """The ``uv`` running this script (``uv run`` exports it as ``UV``), else the one on PATH."""
    found = os.environ.get("UV") or shutil.which("uv")
    if not found:
        raise MeasurementError("uv is not on PATH; the non-editable environment cannot be built.")
    if not Path(found).is_file():
        raise MeasurementError(
            f"uv executable {found} does not exist; the non-editable environment cannot be built.",
        )
    return found


def _run(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    """Run one child to completion, or raise when it cannot start or its output is not UTF-8."""
    try:
        return subprocess.run(
            list(argv),
            cwd=cwd,
            env=dict(env),
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as error:
        raise MeasurementError(f"Cannot start {argv[0]}: {error}") from error
    except UnicodeDecodeError as error:
        raise MeasurementError(f"{argv[0]} printed output that is not UTF-8: {error}") from error


def build_environment(environment: Path) -> None:
    """Install the package non-editable, with the lock's default groups, into ``environment``."""
    completed = _run(
        [
            _uv_executable(),
            "sync",
            "--frozen",
            "--no-editable",
            "--reinstall-package",
            DISTRIBUTION,
            "--python",
            sys.executable,
            "--project",
            str(REPO_ROOT),
            "--quiet",
        ],
        cwd=REPO_ROOT,
        env=child_environment(os.environ, UV_PROJECT_ENVIRONMENT=str(environment)),
    )
    if completed.returncode != 0:
        raise MeasurementError(
            f"uv sync into {environment} failed ({completed.returncode}):\n"
            f"{completed.stdout}{completed.stderr}",
        )


def checked_python_version() -> str:
    """Return ``[tool.basedpyright] pythonVersion``, the Python the package checkers read."""
    import tomllib  # Python 3.11+: the gate runs on the lint interpreter, never the floor cell.

    pyproject = REPO_ROOT / "pyproject.toml"
    try:
        config = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        return str(config["tool"]["basedpyright"]["pythonVersion"])
    except (OSError, KeyError, tomllib.TOMLDecodeError) as error:
        raise MeasurementError(
            f"[tool.basedpyright] pythonVersion is unreadable from {pyproject}: {error!r}",
        ) from error


def run_verifier(environment: Path, cwd: Path) -> dict[str, object]:
    """Run the environment's ``basedpyright --verifytypes`` from ``cwd`` and parse its report."""
    bin_dir = environment / ("Scripts" if os.name == "nt" else "bin")
    executable = bin_dir / ("basedpyright.exe" if os.name == "nt" else "basedpyright")
    if not executable.is_file():
        raise MeasurementError(
            f"{executable} does not exist; the environment build installed no basedpyright.",
        )
    completed = _run(
        [
            str(executable),
            "--verifytypes",
            PACKAGE,
            "--ignoreexternal",
            "--pythonversion",
            checked_python_version(),
            "--outputjson",
        ],
        cwd=cwd,
        env=child_environment(
            os.environ,
            VIRTUAL_ENV=str(environment),
            PATH=os.pathsep.join([str(bin_dir), os.environ.get("PATH", "")]),
        ),
    )
    try:
        return parse_report(completed.stdout)
    except MeasurementError as error:
        raise MeasurementError(f"{error}\nstderr: {completed.stderr[:2000]}") from error


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments (none beyond ``--help``: the run has one shape)."""
    parser = argparse.ArgumentParser(
        description=(
            "Build a non-editable environment and require a 100% basedpyright "
            "--verifytypes score with zero diagnostics for the package's public API."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Measure the installed package's type completeness and judge it."""
    parse_args(sys.argv[1:] if argv is None else argv)
    with tempfile.TemporaryDirectory(prefix="dsf-verifytypes-") as scratch:
        root = Path(scratch).resolve()
        if root == REPO_ROOT or REPO_ROOT in root.parents:
            raise MeasurementError(
                f"The temporary directory {root} lies inside the repository; point TMPDIR "
                "outside it so the verifier reads the installed package.",
            )
        environment = root / "env"
        build_environment(environment)
        report = run_verifier(environment, cwd=root)
    verdict = verdict_for(report)
    for line in format_report(verdict):
        print(line)
    return 0 if verdict.passing else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MeasurementError as error:
        print(error, file=sys.stderr)
        raise SystemExit(2) from error
