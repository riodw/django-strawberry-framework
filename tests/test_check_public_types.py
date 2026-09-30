"""Script tests for the public-API type-completeness gate in ``scripts/check_public_types.py``.

Repo tooling: these rows pin the gate's verdict and its report rendering on
small inline ``basedpyright --verifytypes --outputjson`` payloads - a passing
report, a per-symbol error, a warning-only report, a score below ``1.0`` with
nothing listed, a general diagnostic beside the measured symbols, and the
allowlist: an exact match is accepted, a diagnostic differing from an entry in
any one field is not, and an entry the report no longer carries fails the run.
Every row passes its own allowlist, so the shipped ``ALLOWED_DIAGNOSTICS`` never
decides one. The cannot-measure rows pin that each such shape raises
``MeasurementError`` (exit ``2``) rather than a verdict or a traceback: a report
that is not JSON or not scored, an entry missing a field, a report that lists no
symbol (never judged, so no allowlist entry reads as stale), a missing ``uv`` or
environment ``basedpyright``, and a child that cannot start or prints non-UTF-8.
No row builds the environment or runs a child process: the measurement's
subprocesses are exercised by running the gate itself. A CLI that reads a type
checker's report has no ``/graphql/`` wire shape, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

import json

import pytest

from scripts import check_public_types


def _report(score, symbols=(), general=()):
    """A ``--outputjson`` payload carrying ``score``, ``symbols`` and ``general`` diagnostics."""
    return json.dumps(
        {
            "version": "1.40.1",
            "generalDiagnostics": list(general),
            "summary": {"errorCount": 0, "warningCount": 0},
            "typeCompleteness": {
                "packageName": "django_strawberry_framework",
                "completenessScore": score,
                "symbols": list(symbols),
            },
        },
    )


def _symbol(name, *diagnostics):
    """One ``typeCompleteness.symbols`` entry carrying ``(severity, message)`` diagnostics."""
    return {
        "category": "variable",
        "name": name,
        "diagnostics": [
            {"file": "", "severity": severity, "message": message}
            for severity, message in diagnostics
        ],
    }


#: A symbol with no diagnostic, so a report carrying it has measured something.
_CLEAN_SYMBOL = _symbol("django_strawberry_framework.logger")

#: A fixture allowlist entry, shaped like the shipped ones.
_WIDGET_WARNING = check_public_types.Diagnostic(
    "django_strawberry_framework.widgets.Widget",
    "warning",
    'No docstring found for class "django_strawberry_framework.widgets.Widget"',
)
_WIDGET_ENTRY = check_public_types.AllowedDiagnostic(_WIDGET_WARNING, "the fixture's reason.")


def _judge(payload, allowlist=()):
    """Parse ``payload`` and judge it against ``allowlist``; return the verdict and its lines."""
    verdict = check_public_types.verdict_for(check_public_types.parse_report(payload), allowlist)
    return verdict, check_public_types.format_report(verdict)


def _widget_symbol(*diagnostics):
    """The fixture entry's symbol, carrying ``diagnostics`` as ``Diagnostic`` values."""
    return _symbol(
        _WIDGET_WARNING.symbol,
        *[(diagnostic.severity, diagnostic.message) for diagnostic in diagnostics],
    )


def test_a_complete_report_with_nothing_listed_passes():
    """Score ``1.0``, symbols all clean: the only shape the gate accepts."""
    verdict, lines = _judge(_report(1.0, [_CLEAN_SYMBOL]))

    assert verdict.failing == ()
    assert verdict.passing
    assert lines[0].endswith("completeness score 100.0000% (1.0)")
    assert lines[-1].startswith("OK:")


def test_a_symbol_error_fails_and_is_printed_with_its_symbol_and_severity():
    """A listed error fails the gate, and its symbol, severity and message are all printed."""
    message = (
        "Type is missing type annotation and could be inferred differently by type checkers"
        '\n\xa0\xa0Inferred type is "Logger"'
    )
    verdict, lines = _judge(
        _report(0.99, [_symbol("django_strawberry_framework.logger", ("error", message))]),
    )

    assert verdict.failing == (
        check_public_types.Diagnostic("django_strawberry_framework.logger", "error", message),
    )
    assert not verdict.passing
    assert lines[1] == (
        "  error: django_strawberry_framework.logger: Type is missing type annotation and "
        "could be inferred differently by type checkers"
    )
    # The addendum's non-breaking-space indent is rendered as plain ASCII.
    assert lines[2] == '      Inferred type is "Logger"'
    assert lines[-1].startswith("FAIL:")


def test_a_warning_alone_fails_even_at_a_complete_score():
    """Warnings count: a missing docstring outside the allowlist fails at a score of ``1.0``."""
    verdict, lines = _judge(_report(1.0, [_widget_symbol(_WIDGET_WARNING)]))

    assert verdict.score == 1.0
    assert verdict.failing == (_WIDGET_WARNING,)
    assert not verdict.passing
    assert lines[1] == (f"  warning: {_WIDGET_WARNING.symbol}: {_WIDGET_WARNING.message}")
    assert lines[-1] == (
        "FAIL: the gate needs a score of exactly 100%, no diagnostic outside the allowlist "
        "and no stale allowlist entry; got 100.0000%, unallowed diagnostics: 1, "
        "stale allowlist entries: 0."
    )


def test_an_allowlisted_diagnostic_passes_and_is_printed_with_its_reason():
    """An exact match is accepted, and the run still shows what it accepted and why."""
    verdict, lines = _judge(_report(1.0, [_widget_symbol(_WIDGET_WARNING)]), [_WIDGET_ENTRY])

    assert verdict.failing == ()
    assert verdict.allowed == (_WIDGET_ENTRY,)
    assert verdict.stale == ()
    assert verdict.passing
    assert lines[1:3] == [
        f"  allowed warning: {_WIDGET_WARNING.symbol}: {_WIDGET_WARNING.message}",
        "      reason: the fixture's reason.",
    ]
    assert lines[-1].startswith("OK:")


@pytest.mark.parametrize("field", ["symbol", "severity", "message"])
def test_a_diagnostic_differing_from_an_entry_in_one_field_fails(field):
    """Only an exact match is ignored: the same symbol's other diagnostics still count.

    The report carries the entry's own diagnostic too, so the entry is not stale
    and the only reason left to fail is the near miss.
    """
    near_miss = _WIDGET_WARNING._replace(**{field: f"{getattr(_WIDGET_WARNING, field)}-other"})
    verdict, lines = _judge(
        _report(1.0, [_widget_symbol(_WIDGET_WARNING), _symbol(near_miss.symbol, near_miss[1:])]),
        [_WIDGET_ENTRY],
    )

    assert verdict.failing == (near_miss,)
    assert verdict.allowed == (_WIDGET_ENTRY,)
    assert verdict.stale == ()
    assert not verdict.passing
    assert lines[-1].startswith("FAIL:")


def test_a_stale_allowlist_entry_fails_a_clean_report():
    """An entry the verifier no longer reports fails the run, so it cannot outlive its cause."""
    verdict, lines = _judge(_report(1.0, [_CLEAN_SYMBOL]), [_WIDGET_ENTRY])

    assert verdict.failing == ()
    assert verdict.stale == (_WIDGET_ENTRY,)
    assert not verdict.passing
    assert lines[1:3] == [
        f"  stale allowlist entry: warning: {_WIDGET_WARNING.symbol}: {_WIDGET_WARNING.message}",
        "      the verifier no longer reports it; delete the entry.",
    ]
    assert lines[-1].endswith("unallowed diagnostics: 0, stale allowlist entries: 1.")


@pytest.mark.parametrize("score", [0.9433962264150944, 0.99999])
def test_a_score_below_one_fails_with_no_diagnostic_listed(score):
    """The score is its own verdict: short of ``1.0`` fails even when no symbol is listed."""
    verdict, lines = _judge(_report(score, [_CLEAN_SYMBOL]))

    assert verdict.failing == ()
    assert not verdict.passing
    assert f"({score!r})" in lines[0]
    assert lines[-1].startswith("FAIL:")


def test_a_general_diagnostic_is_reported_ahead_of_the_symbols():
    """A general diagnostic beside measured symbols fails, and is listed first."""
    general = {"file": "", "severity": "error", "message": "Package could not be analyzed"}
    verdict, lines = _judge(
        _report(
            0,
            [_symbol("django_strawberry_framework.logger", ("error", "Type unknown"))],
            general=[general],
        ),
    )

    assert verdict.failing[0] == check_public_types.Diagnostic(
        check_public_types.GENERAL_SYMBOL,
        "error",
        "Package could not be analyzed",
    )
    assert len(verdict.failing) == 2
    assert not verdict.passing
    assert lines[1] == "  error: <general>: Package could not be analyzed"


@pytest.mark.parametrize(
    "payload",
    [
        "Could not resolve module",
        json.dumps(["not", "an", "object"]),
        json.dumps({"generalDiagnostics": []}),
        json.dumps({"typeCompleteness": {"completenessScore": "1.0"}}),
        json.dumps({"typeCompleteness": {"completenessScore": True}}),
    ],
)
def test_output_that_is_not_a_scored_report_is_a_measurement_error(payload):
    """No report, or one without a numeric score, cannot be judged: it never passes silently."""
    with pytest.raises(check_public_types.MeasurementError):
        check_public_types.completeness_score(check_public_types.parse_report(payload))


def test_child_environments_drop_every_redirect_and_take_the_temporary_one():
    """The caller's virtualenv, import path and uv project redirects never reach a child."""
    inherited = dict.fromkeys(check_public_types.REDIRECTING_VARIABLES, "/caller")
    inherited["PATH"] = "/usr/bin"

    env = check_public_types.child_environment(inherited, VIRTUAL_ENV="/tmp/env")

    assert env == {"PATH": "/usr/bin", "VIRTUAL_ENV": "/tmp/env"}


@pytest.mark.parametrize(
    ("general", "reason_lines"),
    [
        (
            [{"file": "", "severity": "error", "message": "No py.typed file found"}],
            ["  error: <general>: No py.typed file found"],
        ),
        ([], ["  (no general diagnostic reported)"]),
    ],
    ids=["no-py-typed", "silent"],
)
def test_a_report_listing_no_symbol_is_a_measurement_error_not_a_stale_allowlist(
    general,
    reason_lines,
):
    """A run that measured nothing is never judged, so no allowlist entry reads as stale."""
    report = check_public_types.parse_report(_report(0, general=general))

    with pytest.raises(check_public_types.MeasurementError) as caught:
        check_public_types.verdict_for(report, [_WIDGET_ENTRY])

    assert str(caught.value).splitlines() == [
        "basedpyright measured no symbol of django_strawberry_framework (score 0.0):",
        *reason_lines,
    ]


@pytest.mark.parametrize(
    ("symbols", "general"),
    [
        ([], [{"file": "", "message": "No py.typed file found"}]),
        ([], [{"file": "", "severity": "error"}]),
        ([{"category": "variable", "diagnostics": []}], []),
        ([{"name": "django_strawberry_framework.logger", "diagnostics": [{"message": "m"}]}], []),
        (
            [
                {
                    "name": "django_strawberry_framework.logger",
                    "diagnostics": [{"severity": "error"}],
                },
            ],
            [],
        ),
        (
            [
                {
                    "name": "django_strawberry_framework.logger",
                    "diagnostics": [{"severity": 1, "message": "m"}],
                },
            ],
            [],
        ),
    ],
    ids=[
        "general-severity",
        "general-message",
        "symbol-name",
        "symbol-severity",
        "symbol-message",
        "non-string",
    ],
)
def test_a_report_entry_missing_a_field_is_a_measurement_error(symbols, general):
    """An entry without its string ``name``, ``severity`` or ``message`` cannot be judged."""
    report = check_public_types.parse_report(_report(1.0, symbols, general=general))

    with pytest.raises(check_public_types.MeasurementError, match="has no string"):
        check_public_types.verdict_for(report, ())


def test_an_environment_without_basedpyright_is_a_measurement_error(tmp_path):
    """A build that installed no verifier fails as a measurement before any child starts."""
    with pytest.raises(check_public_types.MeasurementError, match="installed no basedpyright"):
        check_public_types.run_verifier(tmp_path / "env", cwd=tmp_path)


def test_a_stale_uv_is_a_measurement_error(monkeypatch, tmp_path):
    """A ``UV`` naming a removed executable fails as a measurement before any child starts."""
    monkeypatch.setenv("UV", str(tmp_path / "uv"))

    with pytest.raises(check_public_types.MeasurementError, match="does not exist"):
        check_public_types.build_environment(tmp_path / "env")


def test_no_uv_at_all_is_a_measurement_error(monkeypatch, tmp_path):
    """No ``UV`` and no ``uv`` on ``PATH`` fails as a measurement before any child starts."""
    monkeypatch.delenv("UV", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))

    with pytest.raises(check_public_types.MeasurementError, match="not on PATH"):
        check_public_types.build_environment(tmp_path / "env")


@pytest.mark.parametrize(
    ("error", "match"),
    [
        (FileNotFoundError(2, "No such file or directory"), "Cannot start /env/bin/basedpyright"),
        (PermissionError(13, "Permission denied"), "Cannot start /env/bin/basedpyright"),
        (UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"), "not UTF-8"),
    ],
    ids=["missing", "not-executable", "not-utf-8"],
)
def test_a_child_that_cannot_start_or_decode_is_a_measurement_error(
    monkeypatch,
    tmp_path,
    error,
    match,
):
    """``subprocess.run``'s start and decode failures surface as a measurement error."""

    def refuse(*args, **kwargs):
        raise error

    monkeypatch.setattr(check_public_types.subprocess, "run", refuse)

    with pytest.raises(check_public_types.MeasurementError, match=match):
        check_public_types._run(["/env/bin/basedpyright", "--version"], cwd=tmp_path, env={})
