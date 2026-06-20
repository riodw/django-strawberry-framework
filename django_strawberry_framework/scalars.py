"""Public GraphQL scalars + the ``strawberry_config()`` schema-config factory.

Today: ``BigInt`` (a package-custom scalar) and ``Upload`` (re-exported from
Strawberry's built-in ``strawberry.file_uploads.scalars`` per
spec-037). Unlike ``BigInt``, ``Upload`` is NOT registered in
``_PACKAGE_SCALAR_MAP``: Strawberry's built-in ``DEFAULT_SCALAR_REGISTRY``
already owns it, so an ``Upload``-annotated field resolves in any schema.

``BigInt`` is a JSON-safe scalar typically used to map Django's 64-bit
integer fields (``BigIntegerField``, ``PositiveBigIntegerField``). It is
technically arbitrary-precision - serialized as a decimal string via Python
``str(int_value)`` so values past GraphQL's signed 32-bit ``Int`` boundary
survive transit without truncation. The strict parser and serializer keep the
wire-level input and output sides symmetric (decimal string in, decimal string
out), even though the in-Python accept-sets differ - the parser additionally
accepts ``int`` for direct-call sites while the serializer rejects ``str`` so a
schema cannot emit a value the parser would reject.
"""

import re
from collections.abc import Mapping
from typing import Any, NewType

import strawberry
from strawberry.file_uploads.scalars import Upload, UploadDefinition
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition

# Re-export Strawberry's built-in ``Upload`` scalar (and its ``UploadDefinition``)
# as the package's public upload scalar (spec-037). ``Upload`` is a
# ``NewType("Upload", bytes)`` already present in Strawberry's
# ``DEFAULT_SCALAR_REGISTRY``, so it resolves in every schema with NO
# ``_PACKAGE_SCALAR_MAP`` entry - the deliberate contrast with the package-custom
# ``BigInt`` (which IS absent from the default registry and so must be mapped).
__all__ = [
    "BigInt",
    "Upload",
    "UploadDefinition",
    "strawberry_config",
]

# Plain ASCII decimal, optional ASCII minus for non-zero values, no leading
# zeroes except "0" itself. Rejects underscores (PEP 515), plus signs, Unicode
# decimal digits, hex / octal / scientific notation, and whitespace.
_BIGINT_STRING_PATTERN = re.compile(r"^(0|-?[1-9][0-9]*)$")


def _parse_bigint(value: Any) -> int:
    """Strict BigInt parser.

    Accepts:
        - Python int (excluding bool)
        - Decimal integer strings matching ``^(0|-?[1-9][0-9]*)$``.

    Rejects (with ValueError):
        - bool (True / False) - bool subclasses int; explicit reject
        - float (1.9, 0.0, -1.0) - would otherwise truncate via int()
        - empty / whitespace-padded strings
        - underscore-separated digits ("1_000")
        - leading-plus strings ("+1")
        - leading-zero strings ("01", "007")
        - "-0" (regex permits "0" only)
        - Unicode (e.g. fullwidth) decimal digit strings
        - non-decimal strings ("abc", "1.9", "1e3", "0x10")
        - None and other types
    """
    if isinstance(value, bool):
        # TRY004 is suppressed on the raise: this parser uniformly raises
        # ValueError for every invalid BigInt input; bool is rejected here
        # (before the int check, since bool is an int subclass) as an invalid
        # *value*, matching the GraphQL scalar parse_value contract.
        raise ValueError("BigInt does not accept boolean values")  # noqa: TRY004
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if not _BIGINT_STRING_PATTERN.fullmatch(value):
            raise ValueError(
                f"BigInt requires a plain ASCII decimal integer string "
                f"(optional leading minus for non-zero, no leading zeroes, "
                f"no underscores, no plus sign, no Unicode digits); got {value!r}",
            )
        return int(value)
    raise ValueError(f"BigInt cannot parse {type(value).__name__}")


def _serialize_bigint(value: Any) -> str:
    """Strict BigInt serializer.

    Accepts:
        - Python int (excluding bool)

    Rejects (with TypeError):
        - bool (True / False) - bool subclasses int; explicit reject
        - float, str, Decimal, None, custom objects, anything else

    Strict on the output side too because BigInt is a public scalar - a
    permissive ``serialize=str`` would let a schema emit values the parser
    rejects, breaking the input/output symmetry contract.
    """
    if isinstance(value, bool):
        raise TypeError(f"BigInt cannot serialize bool value {value!r}")
    if isinstance(value, int):
        return str(value)
    raise TypeError(f"BigInt cannot serialize {type(value).__name__}")


BigInt = NewType("BigInt", int)

_BIGINT_SCALAR_DEFINITION: ScalarDefinition = strawberry.scalar(
    name="BigInt",
    serialize=_serialize_bigint,
    parse_value=_parse_bigint,
)

_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition] = {
    BigInt: _BIGINT_SCALAR_DEFINITION,
}


def strawberry_config(
    *,
    extra_scalar_map: Mapping[object, ScalarDefinition] | None = None,
    **config_kwargs: Any,
) -> StrawberryConfig:
    """Build a fresh ``StrawberryConfig`` registering django-strawberry-framework scalars.

    The returned config carries ``_PACKAGE_SCALAR_MAP`` merged with the
    caller's ``extra_scalar_map``; pass it as ``strawberry.Schema(query=...,
    config=strawberry_config(), extensions=[...])``.

    The keyword-only ``extra_scalar_map`` lets consumers register their own
    scalars alongside the package defaults; collisions with package-defined
    keys raise ``ValueError`` (per spec-025 Decision 4). Every other keyword
    argument in ``**config_kwargs`` is forwarded verbatim to
    ``StrawberryConfig(...)`` (e.g. ``auto_camel_case``, ``relay_max_results``).
    Passing ``scalar_map=`` directly is rejected with ``ValueError`` because
    the helper owns that field; route consumer scalars through
    ``extra_scalar_map=`` instead.
    """
    if "scalar_map" in config_kwargs:
        raise ValueError(
            "strawberry_config() owns scalar_map; pass consumer scalars with extra_scalar_map=...",
        )
    extra = dict(extra_scalar_map) if extra_scalar_map else {}
    collisions = _PACKAGE_SCALAR_MAP.keys() & extra.keys()
    if collisions:
        raise ValueError(
            "strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: "
            f"{', '.join(sorted(getattr(k, '__name__', repr(k)) for k in collisions))}. "
            "Define a Strawberry custom scalar of a different NewType / class "
            "to register under a separate key.",
        )
    merged: dict[object, ScalarDefinition] = dict(_PACKAGE_SCALAR_MAP)
    merged.update(extra)
    return StrawberryConfig(scalar_map=merged, **config_kwargs)
