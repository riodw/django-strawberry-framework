"""String-case helpers for the GraphQL <-> Django name boundary.

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


@functools.lru_cache(maxsize=2048)
def snake_case(name: str) -> str:
    """Convert a strict ``camelCase`` GraphQL name back to ``snake_case``.

    Strawberry's default name converter emits ``camelCase`` from
    ``snake_case`` Python attributes; reversing it lets us look up the
    corresponding Django field name without an extra mapping.

    Memoized (``lru_cache``): the optimizer walker reverses the same
    selection names every request over a small fixed vocabulary (the
    schema's GraphQL field names), so the char-by-char rebuild is cached
    rather than recomputed per selection per walk. Pure ``str -> str``,
    so caching is always safe.

    Strict ``camelCase`` only - acronyms are *not* handled.  An input
    like ``"HTMLParser"`` becomes ``"h_t_m_l_parser"`` because each
    upper-case letter triggers a boundary; this is unreachable through
    Strawberry's documented call chain (Python attrs would already be
    ``html_parser``) but is documented here so a future direct caller
    is not surprised.

    Examples:
        ``"name"`` -> ``"name"``;
        ``"isPrivate"`` -> ``"is_private"``;
        ``"createdDate"`` -> ``"created_date"``.
    """
    out: list[str] = []
    for i, c in enumerate(name):
        if i > 0 and c.isupper():
            out.append("_")
        out.append(c.lower())
    return "".join(out)


def pascal_case(name: str) -> str:
    """Convert a ``snake_case`` Django field name to ``PascalCase``.

    Adjacent / leading / trailing underscores collapse to nothing, which
    keeps generated GraphQL type names stable when consumers use names
    like ``_legacy_id`` or ``status_``.

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
        ``"_leading"`` -> ``"Leading"``;
        ``"double__underscore"`` -> ``"DoubleUnderscore"``.
    """
    return "".join(part.capitalize() for part in name.split("_") if part)


def pascal_case_or_raise(name: str, *, make_error: Callable[[str], Exception]) -> str:
    """``pascal_case`` with the shared no-word-token guard (feedback P2.2).

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

    Splits on ``_`` and drops empty tokens; returns ``name`` unchanged when it
    has no word tokens (``""`` -> ``""``, ``"_"`` -> ``"_"``).
    """
    parts = [part for part in name.split("_") if part]
    if not parts:
        return name
    head, *rest = parts
    return head + "".join(part.capitalize() for part in rest)


def flatten_lookup_path(name: str) -> str:
    """Flatten a Django ``LOOKUP_SEP`` path into a single identifier token (DRY review A9).

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
    return name.replace("__", "_")
