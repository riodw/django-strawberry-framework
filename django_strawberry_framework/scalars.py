"""Public scalars defined by django-strawberry-framework.

Today: ``BigInt``. Future scalars (e.g. ``Upload`` per TODO-ALPHA-027) land here.

``BigInt`` is a JSON-safe scalar typically used to map Django's 64-bit
integer fields (``BigIntegerField``, ``PositiveBigIntegerField``). It is
technically arbitrary-precision — serialized as a decimal string via Python
``str(int_value)`` so values past GraphQL's signed 32-bit ``Int`` boundary
survive transit without truncation. The strict parser / serializer keep the
input and output sides symmetric.
"""

import re
import warnings
from typing import Any, NewType

import strawberry

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
        - bool (True / False) — bool subclasses int; explicit reject
        - float (1.9, 0.0, -1.0) — would otherwise truncate via int()
        - empty / whitespace-padded strings
        - underscore-separated digits ("1_000")
        - leading-plus strings ("+1")
        - leading-zero strings ("01", "007")
        - "-0" (regex permits "0" only)
        - Unicode decimal digits ("１２")
        - non-decimal strings ("abc", "1.9", "1e3", "0x10")
        - None and other types
    """
    if isinstance(value, bool):
        raise ValueError("BigInt does not accept boolean values")
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
        - bool (True / False) — bool subclasses int; explicit reject
        - float, str, Decimal, None, custom objects, anything else

    Strict on the output side too because BigInt is a public scalar — a
    permissive ``serialize=str`` would let a schema emit values the parser
    rejects, breaking the input/output symmetry contract.
    """
    if isinstance(value, bool):
        raise TypeError(f"BigInt cannot serialize bool value {value!r}")
    if isinstance(value, int):
        return str(value)
    raise TypeError(f"BigInt cannot serialize {type(value).__name__}")


# Strawberry emits `DeprecationWarning: Passing a class to strawberry.scalar() is
# deprecated. Use StrawberryConfig.scalar_map instead...` whenever a class or
# NewType-backed type is passed directly to strawberry.scalar(...). The
# warning-free migration is roadmapped as TODO-ALPHA-045-0.0.7 (Warning-free
# scalar registration via StrawberryConfig.scalar_map). That card will introduce
# a package-side `strawberry_config(...)` factory and remove this suppression
# block entirely. For 0.0.6, the deprecation is suppressed at the definition
# site so consumers importing django_strawberry_framework see no warning. A
# regression test (test_package_import_does_not_emit_strawberry_deprecation_warning)
# pins the no-leak contract; if the suppression is accidentally removed or
# Strawberry tightens the deprecation, the test catches it.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="Passing a class to strawberry.scalar",
        category=DeprecationWarning,
    )
    BigInt = strawberry.scalar(
        NewType("BigInt", int),
        name="BigInt",
        serialize=_serialize_bigint,
        parse_value=_parse_bigint,
    )
