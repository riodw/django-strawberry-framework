"""GraphQL/Django naming helpers for case conversion and lookup-path flattening.

Every name transform the package applies at the GraphQL/Django boundary:

- ``graphql_camel_name`` maps a Python attribute to the ``camelCase`` GraphQL
  name of a generated input field (filter, order, form, serializer and model
  mutation inputs), injective over lowercase snake-case identifiers.
- ``snake_case`` maps a ``camelCase`` GraphQL name back to ``snake_case``; the
  optimizer walker reverses each selection name with it to find the Django
  field, then matches the forward name where the reversal is lossy.
- ``pascal_case`` builds ``PascalCase`` type-name stems from field names and
  lookup paths (``<TypeName><FieldName>Enum`` choice enums, per-field filter
  and order input types); ``pascal_case_or_raise`` adds the guard against an
  empty stem.
- ``flatten_lookup_path`` collapses a ``LOOKUP_SEP`` path into one identifier
  token.
"""

import functools
from collections.abc import Callable

from django_strawberry_framework.exceptions import ConfigurationError, _safe_type_name

__all__ = (
    "flatten_lookup_path",
    "graphql_camel_name",
    "pascal_case",
    "pascal_case_or_raise",
    "snake_case",
)


def _plain_text(value: object) -> str:
    """Return ``value`` as an exact ``str``; raise ``ConfigurationError`` for a non-string.

    A ``str`` subclass is copied through ``str.__str__`` so its overridden
    ``__hash__`` / ``split`` / ``replace`` never run inside these helpers or the
    ``lru_cache``. The exact-``str`` test runs first: it is every call the
    optimizer walker makes.
    """
    if type(value) is str:
        return value
    if not isinstance(value, str):
        raise ConfigurationError(
            f"String helper input must be a string; got {_safe_type_name(value)}.",
        )
    return str.__str__(value)


@functools.lru_cache(maxsize=2048)
def _snake_case_cached(name: str) -> str:
    """Convert ``name`` to ``snake_case``; the memoized body behind ``snake_case``."""
    out: list[str] = []
    i = 0
    while i < len(name):
        c = name[i]
        if (
            i > 0
            and name[i - 1].isupper()
            and c == "_"
            and i + 3 < len(name)
            and name[i + 1] == "_"
            and name[i + 2] == "x"
            and name[i + 3].isupper()
        ):
            # ``graphql_camel_name`` reserves ``__x`` before an uppercase
            # segment to encode adjacent one-letter snake segments
            # (``a_a_a`` -> ``aA__xA``). Consume that marker as one source
            # separator and let the following uppercase letter supply the
            # segment's first character without adding a second separator.
            out.extend(("_", name[i + 3].lower()))
            i += 4
            continue
        previous = name[i - 1] if i > 0 else ""
        following = name[i + 1] if i + 1 < len(name) else ""
        if (
            c.isupper()
            and i > 0
            and (
                previous.islower()
                or previous.isdigit()
                or previous == "_"
                or (previous.isupper() and following.islower())
            )
        ):
            out.append("_")
        out.append(c.lower())
        i += 1
    return "".join(out)


@functools.wraps(
    _snake_case_cached,
    assigned=("__module__", "__annotations__"),
)
def snake_case(name: str) -> str:
    """Convert a ``camelCase`` / ``PascalCase`` GraphQL name to ``snake_case``.

    Exact inverse of ``graphql_camel_name`` over lowercase snake-case
    identifiers, including leading, trailing and repeated underscores and the
    ``__x`` marker that function writes between adjacent one-letter segments
    (``"aA__xA"`` -> ``"a_a_a"``); that marker is the one place underscores are
    consumed rather than preserved.

    Strawberry's default ``to_camel_case`` names model fields and loses
    boundaries this cannot recover: a digit-leading segment (``isbn_10`` ->
    ``isbn10``), adjacent one-letter segments (``is_a_b`` -> ``isAB``), a
    leading underscore (``_legacy_id`` -> ``LegacyId``) and an upper-case
    letter the Django name already carries (``isPublic`` stays ``isPublic``,
    which reverses to ``is_public``). A caller that must resolve every
    selection also matches the forward name
    (``optimizer/walker.py::_field_by_graphql_name``).

    Acronym runs stay together and split before their final title-cased word
    (``"HTTPServer"`` -> ``"http_server"``); a digit attaches to the token
    before it (``"HTTPServer2API"`` -> ``"http_server2_api"``).

    ``name`` is normalized to an exact ``str`` before the bounded ``lru_cache``
    (2048 entries) is consulted: the walker reverses the same small vocabulary
    of schema field names on every plan build (a plan-cache miss, or an
    uncacheable plan once per execution). ``cache_clear``, ``cache_info`` and
    ``cache_parameters`` are that cache's controls.

    Examples:
        ``"name"`` -> ``"name"``;
        ``"isPrivate"`` -> ``"is_private"``;
        ``"HTTPServer2API"`` -> ``"http_server2_api"``;
        ``"_legacyId"`` -> ``"_legacy_id"``.
    """
    return _snake_case_cached(_plain_text(name))


snake_case.cache_clear = _snake_case_cached.cache_clear
snake_case.cache_info = _snake_case_cached.cache_info
snake_case.cache_parameters = _snake_case_cached.cache_parameters


def pascal_case(name: str) -> str:
    """Convert a ``snake_case`` field name or ``LOOKUP_SEP`` path to ``PascalCase``.

    Leading and trailing underscore runs are preserved verbatim
    (``"_leading"`` -> ``"_Leading"``, ``"status_"`` -> ``"Status_"``), the
    Pascal dual of ``graphql_camel_name``'s edge rule: members of one set
    whose names differ only at the underscore edges (``price`` / ``price_`` /
    ``_price``) stay distinct as Python attrs and camel GraphQL field names,
    so their generated type-name stems must stay distinct too -- otherwise
    two operator-bag / range / enum classes silently claim one GraphQL type
    name and Strawberry keeps whichever registers first, dropping the other
    member's lookups from the schema.

    Interior underscore runs collapse (``"double__underscore"`` ->
    ``"DoubleUnderscore"``), so a ``LOOKUP_SEP`` path PascalCases segment by
    segment (``"category__name"`` -> ``"CategoryName"``, the stem
    ``ClassBasedTypeNameMixin.type_name_for`` builds); the digit rule below
    pins the one interior boundary capitalization cannot encode.

    A separator before a digit-leading segment is retained (``"field_2"``
    -> ``"Field_2"``, not ``"Field2"``) because capitalization cannot encode
    that boundary. This completes the Pascal dual of ``graphql_camel_name``'s
    injectivity rule: without it, ``field_2`` and ``field2`` both become
    ``Field2``, so per-field operator-bag / range / enum type names silently
    collide and Strawberry keeps whichever class registers first.

    Per-segment ``str.capitalize()`` lower-cases every character after the
    first, so acronyms are not preserved (``"my_HTTP_response"`` ->
    ``"MyHttpResponse"``) and names differing only in letter case share a stem
    (``my_HTTP`` / ``my_http`` -> ``MyHttp``); Django and DRF accept
    upper-case field names, so the stem is injective only over lowercase
    input.

    An input with no word-character tokens (``""``, ``"_"``, ``"__"``)
    returns ``""``; ``pascal_case_or_raise`` turns that into the consumer's
    typed error rather than letting an empty stem collide with the root
    type name.

    Examples:
        ``"is_active"`` -> ``"IsActive"``;
        ``"status"`` -> ``"Status"``;
        ``"payment_method"`` -> ``"PaymentMethod"``;
        ``"field_2"`` -> ``"Field_2"``;
        ``"field2"`` -> ``"Field2"``;
        ``"_leading"`` -> ``"_Leading"``;
        ``"trailing_"`` -> ``"Trailing_"``;
        ``"___x_foo"`` -> ``"___XFoo"``;
        ``"double__underscore"`` -> ``"DoubleUnderscore"``.
    """
    name = _plain_text(name)
    parts = [part for part in name.split("_") if part]
    if not parts:
        return ""
    head, *rest = parts
    stem = head.capitalize() + "".join(
        f"_{part}" if part[0].isdigit() else part.capitalize() for part in rest
    )
    leading = name[: len(name) - len(name.lstrip("_"))]
    trailing = name[len(name.rstrip("_")) :]
    return f"{leading}{stem}{trailing}"


def pascal_case_or_raise(name: str, *, make_error: Callable[[str], Exception]) -> str:
    """Return ``pascal_case(name)``, raising ``make_error(name)`` when it is empty.

    Single-sites the no-token check both consumers wrap:
    ``sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`` and
    ``filters/inputs.py::_pascal_case``. ``pascal_case`` returns ``""`` for an
    input with no word-character tokens (``""``, ``"_"``, ``"__"``), which
    would silently collide on downstream generated type names; ``make_error``
    keeps each consumer's error type and message consumer-specific while the
    emptiness check itself stays here.
    """
    pascal = pascal_case(name)
    if not pascal:
        raise make_error(name)
    return pascal


def graphql_camel_name(name: str) -> str:
    """Convert a snake-case Python attribute to its ``camelCase`` GraphQL name.

    ``galaxy_name`` -> ``galaxyName``: the head segment is kept as written;
    each later segment is ``str.capitalize``-d.

    Leading and trailing underscores are preserved, and an empty token between
    words becomes one literal underscore. A separator before a digit-leading
    segment is also retained because capitalization cannot encode that boundary.
    When adjacent segments would create an uppercase run (``a_a_a``), the
    additional separator is encoded as ``__x``; ``snake_case`` reads that
    marker as a separator only between two uppercase characters. This keeps the
    transform injective over normalized snake-case identifiers instead of
    collapsing ``"_legacy_id"`` into ``"legacyId"``, ``"double__name"`` into
    ``"doubleName"``, or ``"field_2"`` into ``"field2"``. An all-underscore
    name passes through unchanged.
    """
    name = _plain_text(name)
    core = name.strip("_")
    if not core:
        return name
    leading = name[: len(name) - len(name.lstrip("_"))]
    trailing = name[len(name.rstrip("_")) :]
    parts = core.split("_")
    head, *rest = parts
    camel = head
    for part in rest:
        if not part or part[0].isdigit():
            camel += f"_{part}"
        else:
            separator = "__x" if camel and camel[-1].isupper() else ""
            camel += f"{separator}{part.capitalize()}"
    return f"{leading}{camel}{trailing}"


def flatten_lookup_path(name: str) -> str:
    """Flatten a Django ``LOOKUP_SEP`` path into a single identifier token.

    ``category__name`` -> ``category_name``: every run of two or more
    underscores becomes one. The one owner of this mangle behind (a)
    python-attr derivation for the generated filter / order input fields, (b)
    the ``check_<field>_permission`` method-name mangle, and (c) the order
    side's aggregate-alias mangle. ``LOOKUP_SEP`` must never survive into a
    generated attribute or alias: Django's ``prefetch_related`` / ``order_by``
    machinery splits on it, the reason generated ``Prefetch`` ``to_attr`` names
    escape it too.
    """
    flattened = _plain_text(name)
    while "__" in flattened:
        flattened = flattened.replace("__", "_")
    return flattened
