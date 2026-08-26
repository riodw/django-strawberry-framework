"""GraphQL/Django naming helpers for case conversion and lookup-path flattening.

Both directions are needed at the GraphQL/Django boundary:

- ``snake_case`` reverses Strawberry's default ``camelCase`` GraphQL field
  names back to the corresponding Django ``snake_case`` model attribute,
  which lets the optimizer (and any future resolver-side code) look up
  Django field metadata without an extra mapping.
- ``pascal_case`` builds GraphQL-friendly type / enum names from Django
  ``snake_case`` field names, used by the choice-to-enum converter to
  produce stable ``<TypeName><FieldName>Enum`` schema names.

Kept minimal on purpose. If a third style (kebab-case, SCREAMING_SNAKE)
ever shows up we'll add it here rather than re-deriving inline at the
call site.
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
    """Normalize a string subclass before invoking string methods or cache machinery."""
    if not isinstance(value, str):
        raise ConfigurationError(
            f"String helper input must be a string; got {_safe_type_name(value)}.",
        )
    if type(value) is str:
        return value
    return str.__str__(value)


@functools.lru_cache(maxsize=2048)
def _snake_case_cached(name: str) -> str:
    """Convert a camel/Pascal GraphQL name back to ``snake_case``.

    Strawberry's default name converter emits ``camelCase`` from
    ``snake_case`` Python attributes; reversing it lets us look up the
    corresponding Django field name without an extra mapping.

    Memoized (``lru_cache``): the optimizer walker reverses the same
    selection names every request over a small fixed vocabulary (the
    schema's GraphQL field names), so the char-by-char rebuild is cached
    rather than recomputed per selection per walk. Pure ``str -> str``,
    so caching is always safe.

    Acronym runs stay together and split before their final title-cased
    word (``"HTTPServer"`` -> ``"http_server"``). Digits stay attached
    to their surrounding token, and existing underscores are preserved;
    the latter makes this the inverse of ``graphql_camel_name`` even for
    leading, trailing, and repeated underscores.

    Examples:
        ``"name"`` -> ``"name"``;
        ``"isPrivate"`` -> ``"is_private"``;
        ``"HTTPServer2API"`` -> ``"http_server2_api"``;
        ``"_legacyId"`` -> ``"_legacy_id"``.
    """
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
    assigned=("__module__", "__doc__", "__annotations__"),
)
def snake_case(name: str) -> str:
    """Normalize ``name`` before consulting the bounded conversion cache."""
    return _snake_case_cached(_plain_text(name))


snake_case.cache_clear = _snake_case_cached.cache_clear
snake_case.cache_info = _snake_case_cached.cache_info
snake_case.cache_parameters = _snake_case_cached.cache_parameters


def pascal_case(name: str) -> str:
    """Convert a ``snake_case`` Django field name to ``PascalCase``.

    Adjacent / leading / trailing underscores collapse to nothing, which
    keeps generated GraphQL type names stable when consumers use names
    like ``_legacy_id`` or ``status_``.

    A separator before a digit-leading segment is retained (``"field_2"``
    -> ``"Field_2"``, not ``"Field2"``) because capitalization cannot encode
    that boundary. This is the Pascal dual of ``graphql_camel_name``'s
    injectivity rule: without it, ``field_2`` and ``field2`` both become
    ``Field2``, so per-field operator-bag / range / enum type names silently
    collide and Strawberry keeps whichever class registers first.

    Strict ``snake_case`` only - acronyms inside a segment are *not*
    preserved.  Per-segment ``str.capitalize()`` upper-cases the first
    character and lower-cases every interior upper-case character, so
    an input like ``"my_HTTP_response"`` becomes ``"MyHttpResponse"``
    rather than ``"MyHTTPResponse"``; this is unreachable through the
    documented call chain (Django field names cannot contain
    upper-case characters) but is documented here so a future direct
    caller is not surprised.  Mirrors the analogous acronym caveat on
    ``snake_case``.

    Examples:
        ``"is_active"`` -> ``"IsActive"``;
        ``"status"`` -> ``"Status"``;
        ``"payment_method"`` -> ``"PaymentMethod"``;
        ``"field_2"`` -> ``"Field_2"``;
        ``"field2"`` -> ``"Field2"``;
        ``"_leading"`` -> ``"Leading"``;
        ``"double__underscore"`` -> ``"DoubleUnderscore"``.
    """
    name = _plain_text(name)
    parts = [part for part in name.split("_") if part]
    if not parts:
        return ""
    head, *rest = parts
    return head.capitalize() + "".join(
        f"_{part}" if part[0].isdigit() else part.capitalize() for part in rest
    )


def pascal_case_or_raise(name: str, *, make_error: Callable[[str], Exception]) -> str:
    """``pascal_case`` with the shared no-word-token guard.

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
    """Lowercase the head, then ``PascalCase`` the rest (``galaxy_name`` -> ``galaxyName``).

    Leading and trailing underscores are preserved, and an empty token between
    words becomes one literal underscore. A separator before a digit-leading
    segment is also retained because capitalization cannot encode that boundary.
    When adjacent segments would create an uppercase run (``a_a_a``), the
    additional separator is encoded as ``__x``; ``snake_case`` reserves that
    marker when it precedes an uppercase segment. This keeps the transform
    injective over normalized snake-case identifiers instead of collapsing
    ``"_legacy_id"`` into ``"legacyId"``, ``"double__name"`` into
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

    ``category__name`` -> ``category_name``: the one owner of the
    ``.replace("__", "_")`` transform behind (a) python-attr derivation for the
    generated filter / order input fields, (b) the ``check_<field>_permission``
    method-name mangle, and (c) the order side's aggregate-alias mangle. The
    transform is load-bearing: ``LOOKUP_SEP`` must never survive into a
    generated attribute or alias (Django's ``prefetch_related`` / ``order_by``
    machinery splits on it - the prefetch ``to_attr`` escaping work exists for
    exactly this class of bug), so when the escaping rules ever change there is
    ONE symbol to grep for, not four inline respellings.
    """
    flattened = _plain_text(name)
    while "__" in flattened:
        flattened = flattened.replace("__", "_")
    return flattened
