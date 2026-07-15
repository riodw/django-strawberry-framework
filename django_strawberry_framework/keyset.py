"""Keyset (value-encoded) stable cursors - the ``Meta.cursor_field`` opt-in.

The BACKLOG ``stable_cursor_field`` contract: a ``DjangoType`` may declare::

    class ItemType(DjangoType):
        class Meta:
            model = Item
            cursor_field = ("-created_at", "id")

and every connection over that type switches from Strawberry's positional
``arrayconnection:N`` offset cursors to VALUE-ENCODED cursors: each edge's
cursor carries the row's ordering-column values (plus the unique terminal
tiebreak), so ``after:`` becomes a tuple-comparison seek
(``WHERE (created_at, id) > (%s, %s)``) instead of a row-number offset -
insert-safe and delete-safe (no cursor drift), and an index seek instead of
numbering-and-discarding ``offset`` rows per page where the fetch strategy
controls the SQL shape (``optimizer/lateral_fetch.py``).

Contract highlights (each enforced in this module or at finalization):

- **Opt-in, never a migration.** ``cursor_field`` unset keeps the shipped
  offset behavior byte-identical. A ``cursor_field`` connection REJECTS
  offset cursors (and vice versa - the prefixes differ), so the two cursor
  vocabularies can never be confused for one another silently.
- **Opaque, tamper-evident payload.** The cursor body is authenticated-encrypted
  with an AES-SIV key derived from ``SECRET_KEY`` (trying
  ``SECRET_KEY_FALLBACKS`` on decrypt, so key rotation keeps live cursors
  valid). A merely signed/base64 cursor encoding ``created_at`` would disclose
  column data from the row it points at; confidentiality is part of the
  contract, not a hardening afterthought. ``cryptography`` is a soft dependency:
  it is imported only when a ``Meta.cursor_field`` connection mints or decodes
  a cursor, with an actionable install error at that boundary. Consequence for
  tests: fixtures MINT cursors and round-trip them - literal cursor bytes are
  never pinned.
- **Deterministic ciphertext.** AES-SIV is deterministic and misuse-resistant:
  identical values under the same order mint identical opaque bytes, preserving
  cross-strategy byte parity. It leaks equality between identical cursor
  positions, never the encrypted ordering values.
- **One canonical codec.** The windowed strategy, the lateral strategy, the
  per-parent fallback pipeline, and root connections all mint and decode
  through THIS module, so a cursor minted by any path replays on every
  other (the cross-strategy byte-parity invariant).
- **Order fingerprint.** The encrypted payload embeds the effective order the
  cursor was minted under; decode rejects replay under a different order
  (a root ``orderBy:`` change between pages) rather than seeking against
  the wrong columns.
- **Portable non-nullable local columns only.** ``cursor_field`` entries must
  be local concrete non-nullable columns ending in a unique column (validated
  at finalization by ``validate_cursor_field_columns``): NULL values poison
  tuple comparisons and their placement diverges across backends (SQLite
  sorts NULLs first ASC, Postgres last), while JSONField comparison semantics
  are backend-specific. The v1 contract excludes both loudly instead of
  paginating wrongly. Root ``orderBy:`` seeks reuse the same rules per
  effective-order column at query time.
- **Permission-aware decode by construction.** The seek predicate is always
  applied to the ALREADY-visibility-scoped queryset (the pipeline runs
  ``get_queryset`` / cascade permissions before any seek), so a cursor
  minted under one viewer's visibility replays under another's without
  leaking rows - positions are recomputed per viewer, and the opaque
  payload discloses no values.

The seek Q-builder adds the redundant leading-bound conjunct
(``a >= x AND (a > x OR (a = x AND ...))``) so the OR-expansion is an index
ACCESS predicate, not just a filter - the standard keyset-pagination lesson
the bare OR-chain misses.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from functools import cache, lru_cache
from types import SimpleNamespace
from typing import Any

from django.conf import settings
from django.core import signing
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models
from django.utils.crypto import salted_hmac
from graphql import GraphQLError
from strawberry.relay.utils import from_base64, to_base64

from .exceptions import ConfigurationError
from .utils.imports import require_optional_module

#: The keyset cursor namespace, package-owned (upstream strawberry uses
#: ``arrayconnection``; strawberry-graphql-django uses ``orderedcursor`` -
#: a distinct prefix keeps all three vocabularies mutually rejecting).
KEYSET_CURSOR_PREFIX = "dstcursor"

#: Domain separation for the AES-SIV key and associated data.
_CURSOR_ENCRYPTION_SALT = "django_strawberry_framework.keyset_cursor"
_CURSOR_ENCRYPTION_CONTEXT = b"django-strawberry-framework keyset cursor v1"
_CRYPTOGRAPHY_INSTALL_HINT = (
    "Meta.cursor_field requires cryptography, which is not installed. Install it "
    "with `pip install 'cryptography>=44.0.0'` (the package's verified AES-SIV floor)."
)


@dataclass(frozen=True)
class CursorColumn:
    """One resolved ordering column of a keyset cursor.

    ``order_ref`` is the Django ``order_by`` string the column came from
    (``"-created_at"``); ``name`` / ``descending`` are its parse;
    ``field`` is the resolved model field (serialization + seek lookups);
    ``value_source`` is the attribute the mint reads the value from - the
    field's ``attname`` for a local column, or the annotation alias a root
    ``orderBy:`` seek attached for a related-path entry.
    """

    order_ref: str
    name: str
    descending: bool
    field: models.Field
    value_source: str


@dataclass(frozen=True)
class KeysetCursor:
    """A decoded keyset cursor: the ordering-column values at one row position."""

    values: tuple[Any, ...]


@dataclass(frozen=True)
class KeysetSeek:
    """One fully-resolved seek: columns + decoded cursor + direction.

    The value the plan-time walker threads to the fetch strategies
    (``NestedConnectionRequest.keyset_seek`` -> ``apply_window_pagination``
    / ``build_lateral_sql``) and the resolve-time slicer builds for the
    root / per-parent paths - one carrier so every consumer renders the
    SAME predicate through ``q()``. ``flip=False`` is the ``after:`` seek
    (rows past the cursor under the effective order); ``flip=True`` the
    ``before:`` seek.
    """

    columns: tuple[CursorColumn, ...]
    cursor: KeysetCursor
    flip: bool = False

    def q(self) -> models.Q:
        """The ORM seek predicate (``keyset_seek_q`` over this carrier)."""
        return keyset_seek_q(self.columns, self.cursor, flip=self.flip)


def order_fingerprint(order_refs: tuple[str, ...]) -> str:
    """The canonical fingerprint of an effective order, embedded in every cursor.

    A plain comma join of the Django ``order_by`` strings: cursors are
    authenticated-encrypted regardless, so the fingerprint stays human-readable
    inside the encrypted payload rather than hashed. Decode compares it against the live
    connection's effective order and rejects a mismatch - a cursor minted
    under ``orderBy: {name: ASC}`` cannot seek a default-ordered page.
    """
    return ",".join(order_refs)


def split_order_ref(order_ref: str, *, owner: str | None = None) -> tuple[str, bool]:
    """Parse one ``order_by`` string into ``(name, descending)``.

    The ``cursor_field`` twin of ``plans.py::order_entry_name_and_direction``'s
    string branch, kept separate because here a malformed entry is a
    CONFIGURATION error (loud), never a fallback signal. This is the single
    syntax owner for both ``types/base.py::_validate_cursor_field`` and
    ``validate_cursor_field_columns``: one optional leading ``-`` followed by
    one local field name, with no relation traversal.
    """
    lead = f"{owner} entry" if owner is not None else "Invalid cursor_field entry:"
    if not isinstance(order_ref, str):
        raise ConfigurationError(f"{lead} {order_ref!r} must be a string.")
    descending = order_ref.startswith("-")
    name = order_ref[1:] if descending else order_ref
    if not name or name.startswith("-"):
        raise ConfigurationError(
            f"{lead} {order_ref!r} is not a valid order string. Expected one optional "
            "leading '-' followed by a local field name.",
        )
    if "__" in name:
        raise ConfigurationError(
            f"{lead} {order_ref!r} traverses a relation; keyset cursor columns must be "
            "local columns.",
        )
    return name, descending


def validate_cursor_field_references(
    order_refs: tuple[str, ...],
    *,
    owner: str,
) -> tuple[tuple[str, bool], ...]:
    """Validate and parse one complete cursor-field reference sequence.

    Both declaration-time normalization and finalization-time column checks
    call this function, so malformed references and duplicate columns cannot
    pass one stage and fail under a different rule at the other.
    """
    if not order_refs:
        raise ConfigurationError(f"{owner} must contain at least one order string.")
    parsed = []
    seen: set[str] = set()
    for order_ref in order_refs:
        name, descending = split_order_ref(order_ref, owner=owner)
        if name in seen:
            raise ConfigurationError(f"{owner} names {name!r} more than once.")
        seen.add(name)
        parsed.append((name, descending))
    return tuple(parsed)


def _resolve_cursor_field_column(model: type[models.Model], name: str) -> models.Field:
    """Resolve one cursor column name to its model field (``pk`` alias honored)."""
    if name == "pk":
        return model._meta.pk
    return model._meta.get_field(name)


def cursor_columns_for(
    model: type[models.Model],
    order_refs: tuple[str, ...],
) -> tuple[CursorColumn, ...]:
    """Resolve validated ``cursor_field`` entries into ``CursorColumn`` specs.

    Assumes ``validate_cursor_field_columns`` passed at finalization; a
    resolution failure here (a model change after finalize) surfaces as the
    loud ``FieldDoesNotExist`` it is.
    """
    columns = []
    for order_ref in order_refs:
        name, descending = split_order_ref(order_ref)
        field = _resolve_cursor_field_column(model, name)
        columns.append(
            CursorColumn(
                order_ref=order_ref,
                name=name,
                descending=descending,
                field=field,
                value_source=field.attname,
            ),
        )
    return tuple(columns)


def validate_cursor_field_columns(
    type_name: str,
    model: type[models.Model],
    cursor_field: tuple[str, ...],
) -> None:
    """Finalization-time column validation for a declared ``Meta.cursor_field``.

    Enforces the v1 column contract (module docstring): every entry resolves
    to a LOCAL CONCRETE NON-NULLABLE column, and the terminal entry is a
    unique total-order anchor (the pk or a ``unique=True`` column) - the
    BACKLOG contract requires the tiebreak DECLARED, not silently appended,
    so the declared order IS the connection order with no hidden tail.
    Raises ``ConfigurationError`` naming the offending entry.
    """
    lead = f"{type_name}.Meta.cursor_field"
    parsed = validate_cursor_field_references(cursor_field, owner=lead)
    for order_ref, (name, _descending) in zip(cursor_field, parsed, strict=True):
        try:
            field = _resolve_cursor_field_column(model, name)
        except FieldDoesNotExist:
            raise ConfigurationError(
                f"{lead} entry {order_ref!r} does not resolve to a field on {model.__name__}.",
            ) from None
        if getattr(field, "is_relation", False) or not getattr(field, "concrete", False):
            raise ConfigurationError(
                f"{lead} entry {order_ref!r} must be a local concrete column; "
                "relation and reverse fields cannot anchor a keyset cursor.",
            )
        if getattr(field, "null", False):
            raise ConfigurationError(
                f"{lead} entry {order_ref!r} is nullable. Keyset cursor columns "
                "must be non-nullable: NULL placement diverges across database "
                "backends and poisons tuple comparisons. Use a non-nullable "
                "column (or a defaulted denormalization of the nullable one).",
            )
        if not _is_supported_cursor_field(field):
            raise ConfigurationError(
                f"{lead} entry {order_ref!r} uses JSONField. Keyset cursor columns "
                "must have portable ordering semantics across database backends; "
                "JSON ordering differs between SQLite and PostgreSQL. Use a scalar "
                "column containing the intended ordering key.",
            )
    terminal_name, _ = parsed[-1]
    terminal = _resolve_cursor_field_column(model, terminal_name)
    if not (terminal.primary_key or getattr(terminal, "unique", False)):
        raise ConfigurationError(
            f"{lead} must end in a unique column so the cursor order is a total "
            f"order; got {cursor_field[-1]!r}. Append the pk (e.g. "
            f"cursor_field = ({', '.join(repr(entry) for entry in cursor_field)}, 'id')).",
        )


def serialize_cursor_value(field: models.Field, value: Any) -> Any:
    """Serialize one ordering-column value through the model field's own codec.

    ``Field.value_to_string`` (fed a shim carrying the value under the
    field's ``attname``) is the field-authored round-trip surface - dates
    isoformat, Decimals via ``str``, floats via shortest-repr ``str`` - and
    ``Field.to_python`` is its documented inverse. Comparison happens only
    in the database as bind parameters, so column collation governs string
    ordering, never Python's.

    ``None`` is rejected here (not passed to ``value_to_string``): Char/Text
    fields stringify ``None`` as the literal ``"None"``, which would mint a
    cursor that seeks the string ``"None"`` and collide with a real row of
    that title. Nullable columns are already excluded at finalization; a
    runtime NULL is a contract violation and must fail loudly.
    """
    if value is None:
        attname = getattr(field, "attname", getattr(field, "name", "?"))
        raise ValueError(f"NULL value for keyset cursor column {attname!r}")
    return field.value_to_string(SimpleNamespace(**{field.attname: value}))


def _deserialize_cursor_value(field: models.Field, raw: Any, argument: str) -> Any:
    """Invert ``serialize_cursor_value``; malformed/non-canonical values raise."""
    try:
        value = field.to_python(raw)
        # Re-serializing after ``to_python`` validates the exact field-authored
        # wire shape. Authenticated payloads cannot be forged, but this still
        # detects model-field drift between mint and decode (and malformed
        # internally minted/test payloads) before a mismatched value reaches SQL.
        if serialize_cursor_value(field, value) != raw:
            raise _invalid_cursor_error(argument)
        return value
    except (TypeError, ValidationError, ValueError):
        raise _invalid_cursor_error(argument) from None


def _invalid_cursor_error(argument: str) -> GraphQLError:
    """The one malformed / tampered / mismatched keyset-cursor error shape."""
    return GraphQLError(
        f"Argument '{argument}' contains an invalid cursor for this connection.",
    )


def _is_supported_cursor_field(field: models.Field) -> bool:
    """Whether ``field`` has portable keyset ordering semantics in the v1 contract."""
    return not isinstance(field, models.JSONField)


@lru_cache(maxsize=1)
def _cursor_crypto_types() -> tuple[Any, type[Exception]]:
    """Load the soft crypto dependency only when keyset cursors are exercised."""
    exceptions = require_optional_module(
        "cryptography.exceptions",
        install_hint=_CRYPTOGRAPHY_INSTALL_HINT,
    )
    aead = require_optional_module(
        "cryptography.hazmat.primitives.ciphers.aead",
        install_hint=_CRYPTOGRAPHY_INSTALL_HINT,
    )
    return aead.AESSIV, exceptions.InvalidTag


@cache
def _cursor_aessiv(secret_key: str | bytes) -> Any:
    """Build and cache the authenticated-encryption primitive for one configured secret.

    The private caller supplies only ``SECRET_KEY`` and ``SECRET_KEY_FALLBACKS``.
    Keeping every configured rotation key avoids an eviction/re-derivation loop
    when a deployment temporarily carries more than three fallbacks.
    """
    aessiv, _invalid_tag = _cursor_crypto_types()
    digest = salted_hmac(
        _CURSOR_ENCRYPTION_SALT,
        _CURSOR_ENCRYPTION_CONTEXT,
        secret=secret_key,
        algorithm="sha512",
    ).digest()
    return aessiv(digest)


def _encrypt_cursor_payload(payload: Any) -> str:
    """Serialize and authenticated-encrypt one cursor payload."""
    serialized = signing.JSONSerializer().dumps(payload)
    encrypted = _cursor_aessiv(settings.SECRET_KEY).encrypt(
        serialized,
        [_CURSOR_ENCRYPTION_CONTEXT],
    )
    return base64.urlsafe_b64encode(encrypted).decode("ascii")


def _decrypt_cursor_payload(value: str, argument: str) -> Any:
    """Decrypt one payload with the active key or any configured fallback."""
    try:
        encrypted = base64.b64decode(
            value.encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (UnicodeEncodeError, binascii.Error, ValueError):
        raise _invalid_cursor_error(argument) from None
    _aessiv, invalid_tag = _cursor_crypto_types()
    secrets = (settings.SECRET_KEY, *settings.SECRET_KEY_FALLBACKS)
    for secret_key in secrets:
        try:
            serialized = _cursor_aessiv(secret_key).decrypt(
                encrypted,
                [_CURSOR_ENCRYPTION_CONTEXT],
            )
        except invalid_tag:
            continue
        try:
            return signing.JSONSerializer().loads(serialized)
        except (TypeError, ValueError):
            raise _invalid_cursor_error(argument) from None
    raise _invalid_cursor_error(argument)


def encode_keyset_cursor(columns: tuple[CursorColumn, ...], row: Any, *, fingerprint: str) -> str:
    """Mint the opaque encrypted cursor for ``row`` under the given effective order.

    Payload shape: ``{"o": <order fingerprint>, "v": [<field-serialized
    values, one per column>]}``, authenticated-encrypted with the project key
    (module docstring), then base64-wrapped under ``KEYSET_CURSOR_PREFIX``
    so bounds derivation can discriminate the cursor vocabulary without
    decrypting the payload first.

    A ``None`` ordering value raises ``GraphQLError`` (same boundary language
    as the ``orderBy:`` nullable-column rejection in ``connection.py``): the
    v1 contract forbids NULL cursor columns, and ``value_to_string(None)`` is
    not a safe encoding for Char/Text fields (it becomes the string ``"None"``).
    """
    values = []
    for column in columns:
        value = getattr(row, column.value_source)
        if value is None:
            raise GraphQLError(
                "This connection uses keyset cursors (Meta.cursor_field), which "
                "require non-nullable ordering columns; a NULL value was read "
                f"from {column.value_source!r}.",
            )
        values.append(serialize_cursor_value(column.field, value))
    encrypted = _encrypt_cursor_payload({"o": fingerprint, "v": values})
    return to_base64(KEYSET_CURSOR_PREFIX, encrypted)


def decode_keyset_cursor(
    value: str,
    columns: tuple[CursorColumn, ...],
    *,
    fingerprint: str,
    argument: str,
) -> KeysetCursor:
    """Verify + decode one ``after:`` / ``before:`` keyset cursor.

    Rejections all surface as the same ``GraphQLError`` (never a crypto
    traceback): non-base64 input, a foreign prefix (an ``arrayconnection``
    offset cursor replayed on a keyset connection), invalid authenticated
    ciphertext (tampering or a rotated-out ``SECRET_KEY``), an
    order-fingerprint mismatch (replay under a different ``orderBy:``), and
    a value-arity or value-shape mismatch. The error is deliberately uniform:
    distinguishing "tampered" from "stale order" would leak oracle detail
    about the opaque payload.
    """
    try:
        prefix, encrypted = from_base64(value)
    except ValueError:
        raise _invalid_cursor_error(argument) from None
    if prefix != KEYSET_CURSOR_PREFIX:
        raise _invalid_cursor_error(argument)
    payload = _decrypt_cursor_payload(encrypted, argument)
    if not isinstance(payload, dict) or payload.get("o") != fingerprint:
        raise _invalid_cursor_error(argument)
    raw_values = payload.get("v")
    if not isinstance(raw_values, list) or len(raw_values) != len(columns):
        raise _invalid_cursor_error(argument)
    return KeysetCursor(
        values=tuple(
            _deserialize_cursor_value(column.field, raw, argument)
            for column, raw in zip(columns, raw_values, strict=True)
        ),
    )


def keyset_seek_q(
    columns: tuple[CursorColumn, ...],
    cursor: KeysetCursor,
    *,
    flip: bool = False,
) -> models.Q:
    """The seek predicate: rows STRICTLY past the cursor position in the total order.

    ``flip=False`` selects rows after the cursor under the effective order
    (the ``after:`` seek); ``flip=True`` selects rows before it (the
    ``before:`` seek) by inverting every per-column comparison. Because the
    terminal column is unique, "strictly past" excludes the cursor row
    itself in both directions.

    Shape: the per-column OR-expansion
    ``a CMP v_a  OR  (a = v_a AND b CMP v_b)  OR  ...`` - the portable form
    that survives mixed ASC/DESC directions where SQL row-value comparison
    cannot - ANDed with the REDUNDANT LEADING BOUND ``a CMP= v_a``. The
    redundant conjunct is load-bearing for the asymptotics: a bare
    OR-expansion is a filter predicate, not an index ACCESS predicate; the
    leading bound lets the composite ``(cursor columns..., pk)`` index seek
    to the cursor position (the use-the-index-luke lesson upstream's
    comparator omits). Columns are non-nullable by contract, so no
    ``isnull`` arms exist.
    """
    seek = models.Q()
    equal_prefix = models.Q()
    for column, value in zip(columns, cursor.values, strict=True):
        greater = column.descending if flip else not column.descending
        op = "gt" if greater else "lt"
        seek |= equal_prefix & models.Q(**{f"{column.name}__{op}": value})
        equal_prefix &= models.Q(**{column.name: value})
    first, first_value = columns[0], cursor.values[0]
    first_greater = first.descending if flip else not first.descending
    bound_op = "gte" if first_greater else "lte"
    return models.Q(**{f"{first.name}__{bound_op}": first_value}) & seek
