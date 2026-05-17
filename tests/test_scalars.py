"""Tests for ``django_strawberry_framework.scalars``.

Covers the ``BigInt`` scalar's strict parser, strict serializer, public
top-level import surface, and the import-time deprecation-suppression
contract. Wire-level / schema-execution behavior lives in
``tests/types/test_converters.py`` per the [`docs/TREE.md`](../docs/TREE.md)
mirror rule (scalar internals here; converter dispatch there).
"""

import subprocess
import sys
from decimal import Decimal

import pytest

from django_strawberry_framework.scalars import _parse_bigint, _serialize_bigint

# ---------------------------------------------------------------------------
# Strict serializer — positive cases
# ---------------------------------------------------------------------------


def test_bigint_serializes_int_as_decimal_string():
    assert _serialize_bigint(42) == "42"


def test_bigint_serializes_zero():
    """``_serialize_bigint(0) == "0"`` — covers the ``int.__bool__ is False`` edge."""
    assert _serialize_bigint(0) == "0"


def test_bigint_serializes_negative_int_as_decimal_string():
    assert _serialize_bigint(-42) == "-42"


def test_bigint_serializes_signed_int64_min():
    """Pin the int64-min boundary value."""
    assert _serialize_bigint(-(2**63)) == "-9223372036854775808"


def test_bigint_serializes_signed_int64_max():
    """Pin the int64-max boundary value."""
    assert _serialize_bigint(2**63 - 1) == "9223372036854775807"


# ---------------------------------------------------------------------------
# Strict serializer — negative cases (B2)
# ---------------------------------------------------------------------------


def test_bigint_serialize_rejects_bool():
    """``True`` and ``False`` both raise ``TypeError``; bool subclasses int."""
    with pytest.raises(TypeError):
        _serialize_bigint(True)
    with pytest.raises(TypeError):
        _serialize_bigint(False)


def test_bigint_serialize_rejects_float():
    """``float`` values raise ``TypeError`` — no implicit truncation via ``str(float)``."""
    with pytest.raises(TypeError):
        _serialize_bigint(1.9)
    with pytest.raises(TypeError):
        _serialize_bigint(0.0)


def test_bigint_serialize_rejects_non_int_types():
    """``str``, ``Decimal``, ``None``, and arbitrary objects all raise ``TypeError``."""
    with pytest.raises(TypeError):
        _serialize_bigint("123")
    with pytest.raises(TypeError):
        _serialize_bigint(Decimal("123"))
    with pytest.raises(TypeError):
        _serialize_bigint(None)

    class _Custom:
        pass

    with pytest.raises(TypeError):
        _serialize_bigint(_Custom())


# ---------------------------------------------------------------------------
# Strict parser — positive cases
# ---------------------------------------------------------------------------


def test_bigint_parses_python_int():
    assert _parse_bigint(42) == 42


def test_bigint_parses_python_zero():
    """``_parse_bigint(0) == 0`` — pins the int-zero branch."""
    assert _parse_bigint(0) == 0


def test_bigint_parses_decimal_string_to_int():
    assert _parse_bigint("42") == 42


def test_bigint_parses_negative_decimal_string_to_int():
    assert _parse_bigint("-42") == -42


def test_bigint_parses_zero_string():
    """``_parse_bigint("0") == 0`` — pins the regex's ``(0|...)`` first alternative."""
    assert _parse_bigint("0") == 0


def test_bigint_parses_signed_int64_min_string():
    """Pin the int64-min boundary string."""
    assert _parse_bigint("-9223372036854775808") == -9223372036854775808


def test_bigint_parses_signed_int64_max_string():
    """Pin the int64-max boundary string."""
    assert _parse_bigint("9223372036854775807") == 9223372036854775807


# ---------------------------------------------------------------------------
# Strict parser — negative cases
# ---------------------------------------------------------------------------


def test_bigint_rejects_python_bool():
    """Both ``True`` and ``False`` raise ``ValueError``."""
    with pytest.raises(ValueError):
        _parse_bigint(True)
    with pytest.raises(ValueError):
        _parse_bigint(False)


def test_bigint_rejects_python_float():
    """Silent-truncation guard: ``int(1.9) == 1`` would otherwise slip through."""
    with pytest.raises(ValueError):
        _parse_bigint(1.9)
    with pytest.raises(ValueError):
        _parse_bigint(0.0)
    with pytest.raises(ValueError):
        _parse_bigint(-1.0)


def test_bigint_rejects_empty_string():
    with pytest.raises(ValueError):
        _parse_bigint("")


def test_bigint_rejects_whitespace_padded_string():
    with pytest.raises(ValueError):
        _parse_bigint(" 123 ")
    with pytest.raises(ValueError):
        _parse_bigint("\t123")


def test_bigint_rejects_non_decimal_string():
    for bad in ("abc", "1.9", "1e3", "0x10"):
        with pytest.raises(ValueError):
            _parse_bigint(bad)


def test_bigint_rejects_underscore_separator():
    """PEP 515-style numeric literals are rejected."""
    with pytest.raises(ValueError):
        _parse_bigint("1_000")
    with pytest.raises(ValueError):
        _parse_bigint("-1_000")


def test_bigint_rejects_leading_plus():
    with pytest.raises(ValueError):
        _parse_bigint("+1")
    with pytest.raises(ValueError):
        _parse_bigint("+0")


def test_bigint_rejects_unicode_decimal_digits():
    """ASCII-only — Unicode decimal digit strings rejected."""
    with pytest.raises(ValueError):
        _parse_bigint("１２")
    with pytest.raises(ValueError):
        _parse_bigint("-１")


def test_bigint_rejects_leading_zeroes():
    for bad in ("01", "007", "-01"):
        with pytest.raises(ValueError):
            _parse_bigint(bad)


def test_bigint_rejects_negative_zero():
    """The regex permits ``"0"`` only — ``"-0"`` is rejected."""
    with pytest.raises(ValueError):
        _parse_bigint("-0")


def test_bigint_rejects_none():
    """Strawberry strips ``null`` before calling ``parse_value`` for nullable inputs,
    so this code path is reachable only through (a) non-nullable inputs where
    Strawberry catches ``None`` before ``_parse_bigint`` runs and (b) direct
    unit-test calls. Tested for defense in depth so a future reader doesn't
    try to remove the parser's ``None`` check as "unreachable".
    """
    with pytest.raises(ValueError):
        _parse_bigint(None)


# ---------------------------------------------------------------------------
# Public-export smoke
# ---------------------------------------------------------------------------


def test_bigint_is_importable_from_top_level():
    """Cheap insurance against an ``__init__.py`` import-order regression.

    Type-shape assertions intentionally avoided — ``ScalarWrapper`` is an
    undocumented internal Strawberry path; schema-execution tests catch
    deeper regressions with stronger signal.
    """
    from django_strawberry_framework import BigInt

    assert BigInt is not None


# ---------------------------------------------------------------------------
# Deprecation-suppression regression (B1)
# ---------------------------------------------------------------------------


def test_package_import_does_not_emit_strawberry_deprecation_warning():
    """Pin that the package import surface is clean of Strawberry's
    class-direct-to-scalar() DeprecationWarning. Subprocess isolation avoids
    the importlib.reload-doesn't-reload-submodules trap.

    ``sys.executable`` is the venv's Python under ``uv run pytest``, so the
    subprocess inherits the editable package install — no PATH / PYTHONPATH
    munging needed.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::DeprecationWarning",
            "-c",
            "import django_strawberry_framework",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, (
        f"Importing the package under -W error::DeprecationWarning failed:\nstderr: {result.stderr}"
    )
