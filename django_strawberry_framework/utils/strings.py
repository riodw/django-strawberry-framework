"""String-case conversion helpers used across the framework.

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


def snake_case(name: str) -> str:
    """Convert a strict ``camelCase`` GraphQL name back to ``snake_case``.

    Strawberry's default name converter emits ``camelCase`` from
    ``snake_case`` Python attributes; reversing it lets us look up the
    corresponding Django field name without an extra mapping.

    Strict ``camelCase`` only — acronyms are *not* handled.  An input
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

    Examples:
        ``"is_active"`` -> ``"IsActive"``;
        ``"status"`` -> ``"Status"``;
        ``"payment_method"`` -> ``"PaymentMethod"``;
        ``"_leading"`` -> ``"Leading"``;
        ``"double__underscore"`` -> ``"DoubleUnderscore"``.
    """
    return "".join(part.capitalize() for part in name.split("_") if part)
