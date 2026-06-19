"""Scalar tests for BigInt and the framework StrawberryConfig helper.

Covers the ``BigInt`` scalar's strict parser, strict serializer, public
top-level import surface, and the import-time deprecation-suppression
contract. Wire-level / schema-execution behavior lives in
``tests/types/test_converters.py`` per the [`docs/TREE.md`](../docs/TREE.md)
mirror rule (scalar internals here; converter dispatch there).
Additionally, two ``strawberry.Schema(query=..., config=strawberry_config())``
integration tests pin the post-migration ``BigInt`` round trip end-to-end
(``test_bigint_serializes_int_via_strawberry_config_schema``,
``test_bigint_parses_decimal_string_via_strawberry_config_schema``).
"""

import subprocess
import sys
from decimal import Decimal
from typing import NewType

import pytest
import strawberry
import strawberry.file_uploads.scalars
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition

from django_strawberry_framework import BigInt, strawberry_config
from django_strawberry_framework.scalars import Upload, _parse_bigint, _serialize_bigint

# ---------------------------------------------------------------------------
# Strict serializer - positive cases
# ---------------------------------------------------------------------------


def test_bigint_serializes_int_as_decimal_string():
    assert _serialize_bigint(42) == "42"


def test_bigint_serializes_zero():
    """``_serialize_bigint(0) == "0"`` - covers the ``int.__bool__ is False`` edge."""
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
# Strict serializer - negative cases (B2)
# ---------------------------------------------------------------------------


def test_bigint_serialize_rejects_bool():
    """``True`` and ``False`` both raise ``TypeError``; bool subclasses int."""
    with pytest.raises(TypeError):
        _serialize_bigint(True)
    with pytest.raises(TypeError):
        _serialize_bigint(False)


def test_bigint_serialize_rejects_float():
    """``float`` values raise ``TypeError`` - no implicit truncation via ``str(float)``."""
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
# Strict parser - positive cases
# ---------------------------------------------------------------------------


def test_bigint_parses_python_int():
    assert _parse_bigint(42) == 42


def test_bigint_parses_python_zero():
    """``_parse_bigint(0) == 0`` - pins the int-zero branch."""
    assert _parse_bigint(0) == 0


def test_bigint_parses_decimal_string_to_int():
    assert _parse_bigint("42") == 42


def test_bigint_parses_negative_decimal_string_to_int():
    assert _parse_bigint("-42") == -42


def test_bigint_parses_zero_string():
    """``_parse_bigint("0") == 0`` - pins the regex's ``(0|...)`` first alternative."""
    assert _parse_bigint("0") == 0


def test_bigint_parses_signed_int64_min_string():
    """Pin the int64-min boundary string."""
    assert _parse_bigint("-9223372036854775808") == -9223372036854775808


def test_bigint_parses_signed_int64_max_string():
    """Pin the int64-max boundary string."""
    assert _parse_bigint("9223372036854775807") == 9223372036854775807


# ---------------------------------------------------------------------------
# Strict parser - negative cases
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
    for bad in (
        "abc",
        "1.9",
        "1e3",
        "0x10",
    ):
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
    """ASCII-only - Unicode decimal digit strings rejected."""
    with pytest.raises(ValueError):
        _parse_bigint("\uff11\uff12")
    with pytest.raises(ValueError):
        _parse_bigint("-\uff11")


def test_bigint_rejects_leading_zeroes():
    for bad in ("01", "007", "-01"):
        with pytest.raises(ValueError):
            _parse_bigint(bad)


def test_bigint_rejects_negative_zero():
    """The regex permits ``"0"`` only - ``"-0"`` is rejected."""
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

    Type-shape assertions intentionally avoided - ``ScalarWrapper`` is an
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
    subprocess inherits the editable package install - no PATH / PYTHONPATH
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


# ---------------------------------------------------------------------------
# strawberry_config() factory - scalar-map tests
# ---------------------------------------------------------------------------


def test_strawberry_config_returns_strawberry_config_instance():
    """The no-arg call returns a ``StrawberryConfig`` instance (Decision 2)."""
    assert isinstance(strawberry_config(), StrawberryConfig)


def test_strawberry_config_default_scalar_map_includes_bigint():
    """The default ``scalar_map`` carries the package-defined ``BigInt`` ScalarDefinition (Decision 3)."""
    cfg = strawberry_config()
    assert BigInt in cfg.scalar_map
    assert isinstance(cfg.scalar_map[BigInt], ScalarDefinition)
    assert cfg.scalar_map[BigInt].name == "BigInt"


def test_strawberry_config_accepts_none_extra_scalar_map():
    """Explicit ``extra_scalar_map=None`` matches the no-arg default."""
    cfg = strawberry_config(extra_scalar_map=None)
    assert len(cfg.scalar_map) == 1
    assert BigInt in cfg.scalar_map


def test_strawberry_config_accepts_empty_extra_scalar_map():
    """``extra_scalar_map={}`` matches ``extra_scalar_map=None`` (edge case)."""
    cfg = strawberry_config(extra_scalar_map={})
    assert len(cfg.scalar_map) == 1
    assert BigInt in cfg.scalar_map


def test_strawberry_config_merges_extra_scalar_map():
    """Consumer-supplied ``extra_scalar_map`` entries merge over the package defaults."""
    CustomScalar = NewType("CustomScalar", str)
    custom_def = strawberry.scalar(name="CustomScalar", serialize=str, parse_value=str)
    cfg = strawberry_config(extra_scalar_map={CustomScalar: custom_def})
    assert len(cfg.scalar_map) == 2
    assert BigInt in cfg.scalar_map
    assert CustomScalar in cfg.scalar_map
    assert cfg.scalar_map[CustomScalar] is custom_def


def test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict():
    """The factory copies ``extra_scalar_map`` rather than mutating the caller's dict (spec #"`extra_scalar_map` mutation post-call")."""
    CustomScalar = NewType("CustomScalar", str)
    custom_def = strawberry.scalar(name="CustomScalar", serialize=str, parse_value=str)
    caller_dict = {CustomScalar: custom_def}
    before = dict(caller_dict)
    strawberry_config(extra_scalar_map=caller_dict)
    assert caller_dict == before


def test_strawberry_config_collision_with_package_scalar_raises_value_error():
    """Collision with a package-defined scalar key raises ``ValueError`` (Decision 4)."""
    alt_def = strawberry.scalar(name="AltBigInt", serialize=str, parse_value=int)
    with pytest.raises(ValueError) as excinfo:
        strawberry_config(extra_scalar_map={BigInt: alt_def})
    message = str(excinfo.value)
    assert "BigInt" in message
    assert "cannot redeclare" in message


def test_strawberry_config_independent_call_returns_independent_instance():
    """Each call returns a fresh ``StrawberryConfig`` with a fresh ``scalar_map`` dict (spec #"Independent return value semantics")."""
    CustomScalar = NewType("CustomScalar", str)
    custom_def = strawberry.scalar(name="CustomScalar", serialize=str, parse_value=str)
    c1 = strawberry_config()
    c2 = strawberry_config()
    assert c1 is not c2
    assert c1.scalar_map is not c2.scalar_map
    c1.scalar_map[CustomScalar] = custom_def
    assert CustomScalar not in c2.scalar_map


# ---------------------------------------------------------------------------
# strawberry_config() factory - **config_kwargs passthrough tests
# ---------------------------------------------------------------------------


def test_strawberry_config_forwards_auto_camel_case_kwarg():
    """``auto_camel_case`` is forwarded; assert on ``name_converter.auto_camel_case``
    because ``auto_camel_case`` is a dataclass ``InitVar`` on ``StrawberryConfig``
    (spec #"`auto_camel_case` is declared as a dataclass `InitVar`" - verified against upstream ``StrawberryConfig.__post_init__``).
    """
    overridden = strawberry_config(auto_camel_case=False)
    assert overridden.name_converter.auto_camel_case is False
    default = strawberry_config()
    assert default.name_converter.auto_camel_case is True


def test_strawberry_config_forwards_relay_max_results_kwarg():
    """``relay_max_results`` (an integer field, structurally distinct from a bool flag)
    is forwarded verbatim to ``StrawberryConfig(...)``.
    """
    cfg = strawberry_config(relay_max_results=200)
    assert cfg.relay_max_results == 200


def test_strawberry_config_combines_extra_scalar_map_and_config_kwargs():
    """Both composition paths cooperate on a single call."""
    CustomScalar = NewType("CustomScalar", str)
    custom_def = strawberry.scalar(name="CustomScalar", serialize=str, parse_value=str)
    cfg = strawberry_config(
        extra_scalar_map={CustomScalar: custom_def},
        relay_max_results=200,
    )
    assert cfg.relay_max_results == 200
    assert BigInt in cfg.scalar_map
    assert CustomScalar in cfg.scalar_map


def test_strawberry_config_rejects_scalar_map_kwarg():
    """``scalar_map=`` is structurally rejected regardless of payload (Error shapes)."""
    with pytest.raises(ValueError) as excinfo_empty:
        strawberry_config(scalar_map={})
    message_empty = str(excinfo_empty.value)
    assert "scalar_map" in message_empty
    assert "extra_scalar_map" in message_empty

    with pytest.raises(ValueError):
        strawberry_config(scalar_map=None)

    alt_def = strawberry.scalar(name="AltBigInt", serialize=str, parse_value=int)
    with pytest.raises(ValueError):
        strawberry_config(scalar_map={BigInt: alt_def})


def test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream():
    """An unknown kwarg surfaces upstream's ``TypeError``; the helper does not swallow it."""
    with pytest.raises(TypeError):
        strawberry_config(this_kwarg_does_not_exist_in_strawberry=True)


# ---------------------------------------------------------------------------
# strawberry_config() factory - integration tests (schema round-trip)
# ---------------------------------------------------------------------------


def test_bigint_serializes_int_via_strawberry_config_schema():
    """An ``int`` returned from a ``BigInt``-typed resolver round-trips as the decimal string."""

    @strawberry.type
    class Q:
        @strawberry.field
        def big(self) -> BigInt:
            return 9_223_372_036_854_775_807  # int64_max

    schema = strawberry.Schema(query=Q, config=strawberry_config())
    result = schema.execute_sync("{ big }")
    assert result.errors is None
    assert result.data == {"big": "9223372036854775807"}


def test_bigint_parses_decimal_string_via_strawberry_config_schema():
    """A decimal-string argument typed ``BigInt`` is parsed and echoed back as the decimal string."""

    @strawberry.type
    class Q:
        @strawberry.field
        def echo(self, value: BigInt) -> BigInt:
            return value

    schema = strawberry.Schema(query=Q, config=strawberry_config())
    result = schema.execute_sync('{ echo(value: "9223372036854775807") }')
    assert result.errors is None
    assert result.data == {"echo": "9223372036854775807"}


# ---------------------------------------------------------------------------
# Upload scalar - re-export + default-registry resolution (spec-037 Decision 5)
# ---------------------------------------------------------------------------


def test_upload_is_strawberry_builtin_re_export_not_a_wrapper():
    """``Upload`` is Strawberry's built-in scalar object, re-exported, not a package wrapper."""
    assert Upload is strawberry.file_uploads.scalars.Upload


def test_upload_is_importable_from_top_level_scalars_module():
    """``Upload`` is importable from ``django_strawberry_framework.scalars`` (root export is Slice 3)."""
    from django_strawberry_framework.scalars import Upload as UploadFromScalars

    assert UploadFromScalars is strawberry.file_uploads.scalars.Upload


def test_strawberry_config_scalar_map_excludes_upload():
    """The package ``scalar_map`` carries ``BigInt`` but NOT ``Upload`` (Decision 5).

    ``Upload`` is absent from ``_PACKAGE_SCALAR_MAP`` because Strawberry's built-in
    ``DEFAULT_SCALAR_REGISTRY`` already owns it; only the package-custom ``BigInt``
    (absent from that registry) needs a map entry.
    """
    scalar_map = strawberry_config().scalar_map
    assert BigInt in scalar_map
    assert Upload not in scalar_map


@strawberry.type
class _UploadQuery:
    @strawberry.field
    def echo_name(self, file: Upload) -> str:
        """A trivial ``Upload``-typed argument forcing the scalar into the schema."""
        return getattr(file, "name", "")


def test_upload_field_resolves_under_strawberry_config_schema():
    """An ``Upload``-typed field builds + appears in the SDL under ``strawberry_config()``."""
    schema = strawberry.Schema(query=_UploadQuery, config=strawberry_config())
    assert "scalar Upload" in str(schema)


def test_upload_field_resolves_under_plain_strawberry_config():
    """An ``Upload``-typed field builds + appears in the SDL under a plain ``StrawberryConfig``.

    This is the load-bearing Decision-5 pin: ``Upload`` rides Strawberry's
    ``DEFAULT_SCALAR_REGISTRY``, so it resolves with NO package config / scalar map.
    """
    schema = strawberry.Schema(query=_UploadQuery, config=StrawberryConfig())
    assert "scalar Upload" in str(schema)
