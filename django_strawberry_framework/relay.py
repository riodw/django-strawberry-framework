"""Root Relay refetch fields - ``DjangoNodeField`` / ``DjangoNodesField``.

The consumer-facing root ``node(id:)`` / ``nodes(ids:)`` surface
(``docs/spec-032-full_relay-0_0_9.md`` Decisions 3/4/5/11). Both factories
return ``strawberry.field(resolver=...)`` values picked up by Strawberry's
class-body walk (the ``DjangoListField`` mechanism) and come in two forms:

- **Bare** - ``node: relay.Node | None = DjangoNodeField()`` /
  ``nodes: list[relay.Node | None] = DjangoNodesField()``: the Relay-spec
  canonical fields; the decoded id may resolve to any registered
  Relay-Node-shaped ``DjangoType``.
- **Typed** - ``genre: GenreType | None = DjangoNodeField(GenreType)``: the
  target is validated at construction time, and an id that decodes to a
  different type raises a ``GraphQLError`` naming the expected and received
  types (Decision 4).

Resolution is **nullable by contract**: dispatch is ``required=False``
unconditionally, so hidden, missing, and uncoercible-pk ids resolve to
``null`` (or a positional ``null`` list entry) and the optional annotation
spelling above is the supported shape (Decision 5). Malformed / undecodable
ids are the other failure family: every ``ConfigurationError`` from
``types/relay.py::decode_global_id`` converts to ``GraphQLError("Invalid
GlobalID: ...", extensions={"code": "GLOBALID_INVALID"})`` at the field
boundary - decode runs on payload data only, before any query, so nothing
leaks row existence.

Type source: the field's schema type comes from the consumer's class-body
annotation at the assignment site, exactly as spelled above - both factories'
resolvers return ``Any``, so there is no framework-side fallback. Omitting the
annotation (``node = DjangoNodeField()``) surfaces at ``strawberry.Schema(...)``
build as graphql-core's ``TypeError: Query fields cannot be resolved.
Unexpected type 'typing.Any'`` - that message means "annotate the assignment".
The typed form does NOT cross-validate the annotation against ``target_type``
(the factory cannot see its assignment site): a mismatched pairing like
``genre: AuthorType | None = DjangoNodeField(GenreType)`` builds a schema, and
every query then rejects ids at runtime with the wrong-node-type
``GraphQLError`` - loud, but late.

The encode/decode internals stay in ``types/relay.py`` (spec-031 Decision 11
reserved this top-level module for the root fields).

Engine note (spec-032 Edge cases): Strawberry only registers schema types it
can reach. A schema whose *only* root field is the interface-typed bare
``node`` must pass its concrete types explicitly via
``strawberry.Schema(types=[...])`` or expose them through other fields - this
is engine behavior, not package-fixable.
"""

from __future__ import annotations

import contextlib
import inspect
from collections.abc import Sequence
from enum import Enum
from typing import Any, NamedTuple

import strawberry
from django.core.exceptions import FieldDoesNotExist, ValidationError
from graphql import GraphQLError
from strawberry.types import Info
from strawberry.utils.inspect import in_async_context

from .exceptions import ConfigurationError
from .list_field import _validate_relay_djangotype_target
from .types.relay import _NODE_TYPE_HINT_ATTR, _model_for, decode_global_id

__all__ = ("DjangoNodeField", "DjangoNodesField")


# Module-level ledger backing the finalize-time no-Node-types check
# (spec-032 Decision 8; the ``_helper_referenced_filtersets`` precedent -
# ``registry.clear()`` co-clears it). Appended by BOTH factories on every
# call; only emptiness is load-bearing, the factory-name entries aid debugging.
_node_fields_declared: list[str] = []


def _decode_or_graphql_error(gid: str) -> tuple[type, str]:
    """Decode ``gid``, converting ``ConfigurationError`` to the wire error.

    Every ``ConfigurationError`` from ``types/relay.py::decode_global_id``
    (malformed base64, non-``type:id`` payload, unresolvable label/name,
    strategy-forbidden shape, no recorded strategy) converts to
    ``GraphQLError`` with the ``GLOBALID_INVALID`` extensions code - the
    ``FilterSet`` ``FILTER_INVALID`` precedent (Decision 5).

    SCOPE IS NARROW (spec-032 Revision 7 P2): this wraps the decode call
    ONLY. The ``resolve_node`` / ``resolve_nodes`` dispatch runs OUTSIDE it,
    because ``SyncMisuseError`` subclasses ``ConfigurationError`` and a
    sync/async-``get_queryset`` misconfiguration must surface as itself,
    never mislabeled ``GLOBALID_INVALID``.
    """
    try:
        return decode_global_id(gid)
    except ConfigurationError as exc:
        raise GraphQLError(
            f"Invalid GlobalID: {exc}",
            extensions={"code": "GLOBALID_INVALID"},
        ) from exc


def _coerce_pk_or_none(resolved_type: type, node_id: str) -> Any:
    """Coerce ``node_id`` to the resolution field's Python type; ``None`` if uncoercible.

    ``decode_global_id`` validates payload SHAPE only, so a well-formed
    ``library.genre:abc`` decodes to ``(GenreType, "abc")``; a raw
    ``qs.filter(<id_attr>="abc")`` against an integer column would leak Django's
    ``ValueError: Field 'id' expected a number``. A coercion failure is treated
    as "identifies no row" -> ``null`` (single) / positional ``null`` hole
    (batch), with no query issued, so the no-existence-oracle property is
    unaffected (Decision 5, Revision 7 P2).

    Coercion is ``to_python`` **then** ``run_validators``: ``to_python`` is a pure
    type cast that does NOT range-check, so a syntactically-numeric but
    out-of-range literal (e.g. ``"9" * 400`` against a 64-bit integer column)
    casts to a Python ``int`` cleanly and would reach the ORM, where SQLite's
    ``pk__in`` parameter binding raises a raw ``OverflowError`` (``Python int too
    large to convert to SQLite INTEGER``). The field's own validators carry the
    backend ``integer_field_range`` Min/MaxValueValidators, so ``run_validators``
    rejects an out-of-range value as a ``ValidationError`` here - the SAME
    "identifies no row" outcome as a non-numeric literal, decided before any query
    so neither the node lookup nor the relation ``pk__in`` visibility query can
    raise a backend ``OverflowError`` (feedback - relation huge-pk crash). A
    column with no range/length validators (a plain string id) is unaffected.

    The coercion field is the SAME one the resolution filters on -
    ``resolved_type.resolve_id_attr()`` (the value
    ``_resolve_node(s)_default`` build their ``{id_attr: ...}`` / ``__in``
    filter from) - NOT ``model._meta.pk``. They coincide for the default
    (``"pk"``) but diverge for a consumer ``id: relay.NodeID[...]`` annotation,
    which makes the id slot a non-pk column (and is the documented composite-pk
    escape hatch where ``_meta.pk`` is a ``CompositePrimaryKey`` with no
    single-column ``to_python``). Coercing against ``_meta.pk`` there would
    mis-type the value (``"007"`` -> ``7`` -> filters ``code=7`` !=``"007"``) or
    spuriously reject an existing row. ``"pk"`` maps to the concrete pk field; a
    NodeID attr that is not a concrete model field skips coercion and passes the
    raw string (pre-032 behavior - Django handles string lookups on the column).
    """
    model = _model_for(resolved_type)
    id_attr = resolved_type.resolve_id_attr()
    if id_attr == "pk":
        field = model._meta.pk
    else:
        try:
            field = model._meta.get_field(id_attr)
        except FieldDoesNotExist:
            return node_id
    try:
        value = field.to_python(node_id)
        field.run_validators(value)
    except (ValueError, ValidationError):
        return None
    return value


def _check_typed_match(target_type: type | None, resolved: type) -> None:
    """Raise the typed-form mismatch ``GraphQLError``; no-op for the bare form.

    Identity comparison (``resolved is not target_type``) on the decoded
    candidate. The error names the expected and received types by their
    consumer-facing ``graphql_type_name`` (honoring ``Meta.name``). It
    deliberately carries NO ``extensions`` code - the spec assigns a code
    only to ``GLOBALID_INVALID`` (Decision 4 / Error shapes).
    """
    if target_type is None or resolved is target_type:
        return
    expected = target_type.__django_strawberry_definition__.graphql_type_name
    received = resolved.__django_strawberry_definition__.graphql_type_name
    raise GraphQLError(
        f"Wrong node type: expected a {expected} id, received a {received} id.",
    )


class GlobalIDDecode(Enum):
    """The outcome code of a typed ``GlobalID`` decode (spec-036 DRY-2).

    A non-raising classification the caller maps to its own error surface
    (``FieldError`` on ``id`` / relation ``FieldError`` / ``GraphQLError``), so the
    decode + model-check + pk-coercion contract is single-sourced while the error
    shape stays caller-specific.
    """

    OK = "ok"
    DECODE_FAILED = "decode_failed"  # malformed / unresolvable type slot.
    WRONG_MODEL = "wrong_model"  # decoded to a type whose model != the expected one.
    UNCOERCIBLE_PK = "uncoercible_pk"  # right model, but node_id is not a valid pk literal.


class DecodeResult(NamedTuple):
    """The structured result of ``decode_model_global_id`` (spec-036 DRY-2).

    ``pk`` is the coerced primary-key value ONLY when ``status is
    GlobalIDDecode.OK`` (``None`` otherwise); ``resolved_type`` is the decoded
    ``DjangoType`` when decode itself succeeded (``None`` when ``DECODE_FAILED``).
    """

    status: GlobalIDDecode
    pk: Any | None
    resolved_type: type | None


def decode_model_global_id(value: Any, expected_model: type) -> DecodeResult:
    """Decode a typed ``GlobalID`` against ``expected_model``, non-raising (spec-036 DRY-2).

    The single source of the mutation typed-id contract the root ``id:`` decode
    (``_coerce_lookup_id``) and the relation ``<field>_id`` decode
    (``_decode_relation_id_set``) both consume: decode the value via
    ``decode_global_id`` (shape-only), verify the resolved type's model **is**
    ``expected_model``, and coerce ``node_id`` through the resolved type's id field
    via ``_coerce_pk_or_none`` (the SAME coercer the node field uses, so an
    uncoercible literal never reaches the ORM as a raw ``ValueError`` - feedback
    CR-1). Returns a :class:`DecodeResult` whose :class:`GlobalIDDecode` status the
    caller maps to its own error surface (this helper never raises a
    ``GraphQLError`` - the node-field raising behavior stays in the node field).
    """
    try:
        resolved_type, node_id = decode_global_id(value)
    except Exception:
        return DecodeResult(GlobalIDDecode.DECODE_FAILED, None, None)
    if _model_for(resolved_type) is not expected_model:
        return DecodeResult(GlobalIDDecode.WRONG_MODEL, None, resolved_type)
    pk = _coerce_pk_or_none(resolved_type, node_id)
    if pk is None:
        return DecodeResult(GlobalIDDecode.UNCOERCIBLE_PK, None, resolved_type)
    return DecodeResult(GlobalIDDecode.OK, pk, resolved_type)


def _validate_node_target(target_type: type, *, field: str) -> None:
    """Run the four shared target guards plus the Relay-Node-shaped fifth guard.

    Thin wrapper over ``list_field.py::_validate_relay_djangotype_target`` -- the
    Relay-shaped target guard shared with ``connection.py::DjangoConnectionField``
    per the 0.0.9 DRY pass. A refetch field has no ``resolver=`` seam, so ``None``
    is passed; ``field`` is interpolated into the messages so each factory
    (``DjangoNodeField`` / ``DjangoNodesField``) names itself.
    """
    _validate_relay_djangotype_target(
        target_type,
        None,
        field=field,
        relay_error_message=(
            f"{field} requires a Relay-Node-shaped DjangoType target; add "
            "`relay.Node` to `Meta.interfaces` (or inherit `relay.Node` directly)"
        ),
    )


def _interleave(
    positions: list[tuple[type, int] | None],
    per_type_results: dict[type, list[Any]],
) -> list[Any]:
    """Reassemble per-type result lists into input order with ``null`` holes.

    ``positions`` carries one entry per input id: ``None`` for an
    uncoercible-pk hole, otherwise ``(decoded_type, within-group index)``.
    Missing/hidden positions are already ``None`` inside each per-type list
    (``_order_nodes`` under ``required=False``). One implementation serves
    both the sync branch and the gathering coroutine.

    Indexing by ``within-group index`` is what makes the per-type
    ``resolve_nodes`` return contract load-bearing - see
    ``_check_nodes_result`` and the ``DjangoNodesField`` override note.
    """
    return [
        None if position is None else per_type_results[position[0]][position[1]]
        for position in positions
    ]


def _check_nodes_result(resolved_type: type, result: Any, pks: list[Any]) -> Any:
    """Validate a ``resolve_nodes`` return is positionally 1:1 with ``pks``.

    ``_interleave`` indexes each result by its within-group position, so a
    consumer ``resolve_nodes`` override that returns an unordered, shrunk, or
    duplicate-collapsed list (the obvious
    ``get_queryset().filter(pk__in=node_ids)`` spelling) would otherwise yield
    silently wrong rows or an ``IndexError``. The cheap structural length check
    converts the shrunk / duplicate-collapsed case into a named
    ``ConfigurationError``; the framework default's ``_order_nodes`` shape
    always satisfies it. (Ordering itself is the documented override contract -
    see ``DjangoNodesField`` - not re-validated here.)

    A generator/iterator return (no ``__len__``) is materialized first so it
    reaches the length check (and ``_interleave``'s positional indexing)
    instead of dying on a bare ``len()`` ``TypeError``.
    """
    if not hasattr(result, "__len__"):
        result = list(result)
    if len(result) != len(pks):
        raise ConfigurationError(
            f"{resolved_type.__name__}.resolve_nodes returned {len(result)} row(s) for "
            f"{len(pks)} requested id(s); a resolve_nodes override must return a list "
            "input-ordered and 1:1 with node_ids (None for missing) - the "
            "_resolve_nodes_default / _order_nodes shape.",
        )
    return result


def _stamp_node_type(resolved_type: type, node: Any) -> Any:
    """Stamp the decode-resolved ``DjangoType`` on a fetched node instance.

    The bare ``node``/``nodes`` fields hand graphql-core a raw model
    instance under the abstract ``Node`` annotation; concrete-type
    selection then runs every candidate type's ``is_type_of``. For a
    model with two registered Relay types, plain
    ``isinstance(obj, (type_cls, model))`` answers ``True`` on BOTH
    candidates and iteration order picks the ``__typename`` - regardless
    of which type the GlobalID named (Round-4 review S2). The stamp
    carries the decode-routing decision through to type resolution;
    ``install_is_type_of``'s closure honors it before the isinstance
    fallback.

    ``None`` (hidden/missing/uncoercible -> ``null``) passes through. A
    consumer ``resolve_node(s)`` override may return a non-model object
    that rejects attribute writes (``__slots__``); the stamp is
    best-effort there - such objects fall back to the pre-032 isinstance
    behavior.
    """
    if node is None:
        return node
    with contextlib.suppress(AttributeError):
        setattr(node, _NODE_TYPE_HINT_ATTR, resolved_type)
    return node


async def _await_and_stamp(resolved_type: type, awaitable: Any) -> Any:
    """Await an async ``resolve_node`` result, then stamp it (async sibling)."""
    return _stamp_node_type(resolved_type, await awaitable)


def DjangoNodeField(  # noqa: N802  # PascalCase for graphene-django parity - consumer usage is `DjangoNodeField(GenreType)`
    target_type: type | None = None,
    *,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
) -> Any:
    """Factory for the root ``node(id: ID!)`` Relay refetch field.

    Bare form (``target_type=None``) resolves any registered Relay-Node-shaped
    ``DjangoType``; the typed form pins one target and rejects mismatched ids
    with a ``GraphQLError``. See the module docstring for the full contract
    (nullable-by-contract dispatch, the ``GLOBALID_INVALID`` boundary, and the
    bare-field ``strawberry.Schema(types=[...])`` engine note).
    """
    if target_type is not None:
        _validate_node_target(target_type, field="DjangoNodeField")
    _node_fields_declared.append("DjangoNodeField")

    def _resolve(
        root: Any,  # noqa: ARG001
        info: Info,
        # ``id`` is the Relay-spec signature (``node(id: ID!)``) - the builtin
        # shadow is deliberate. ``strawberry.ID`` (the raw string), never
        # ``relay.GlobalID``: a GlobalID-annotated argument is parsed by
        # Strawberry's ``convert_argument`` BEFORE the resolver runs, so
        # malformed ids would never reach the package (Revision 7 P1).
        id: strawberry.ID,  # noqa: A002
    ) -> Any:
        resolved, node_id = _decode_or_graphql_error(id)
        # Everything below runs OUTSIDE the decode try/except so a dispatch-time
        # ``SyncMisuseError`` surfaces as itself (see ``_decode_or_graphql_error``).
        _check_typed_match(target_type, resolved)
        pk = _coerce_pk_or_none(resolved, node_id)
        if pk is None:
            # Uncoercible literal -> null with no query issued (Revision 7 P2).
            return None
        # In async context ``resolve_node`` returns a coroutine Strawberry's
        # executor awaits as a plain-field return (Edge cases "Async
        # end-to-end") - the stamp then rides inside ``_await_and_stamp``.
        # Calling the classmethod (not the underscore default) preserves
        # consumer overrides for free.
        result = resolved.resolve_node(pk, info=info, required=False)
        if inspect.isawaitable(result):
            return _await_and_stamp(resolved, result)
        return _stamp_node_type(resolved, result)

    return strawberry.field(
        resolver=_resolve,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )


def DjangoNodesField(  # noqa: N802  # PascalCase for graphene-django parity - consumer usage is `DjangoNodesField(GenreType)`
    target_type: type | None = None,
    *,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
) -> Any:
    """Factory for the root ``nodes(ids: [ID!]!)`` batch Relay refetch field.

    Input order is preserved; positional ``null`` is reserved for
    well-formed-but-invisible/missing/uncoercible ids; a malformed id (or a
    wrong-type id under the typed form) ANYWHERE fails the WHOLE field - the
    ``[Node]!`` non-null nulls the enclosing ``data`` (Decision 5). Duplicate
    ids resolve per position, and resolution is batched per distinct decoded
    type (one ``resolve_nodes`` call each - Decision 4).

    Consumer ``resolve_nodes`` override contract: this field calls the
    ``resolve_nodes`` *classmethod* (preserving consumer overrides), then
    re-assembles results by position. An override MUST return a list
    input-ordered and 1:1 with the ``node_ids`` it received, with ``None`` for
    missing ids - the ``_resolve_nodes_default`` / ``_order_nodes`` shape (and
    the same positional assumption Strawberry's native batch resolver makes).
    The obvious ``get_queryset().filter(pk__in=node_ids)`` spelling violates
    this (unordered, shrunk for missing ids, IndexError on duplicates); the
    ``AwaitableOrValue`` return (sync list or coroutine) is accepted, and a
    wrong-length return is rejected with a ``ConfigurationError`` naming the
    type rather than producing silently wrong rows.
    """
    if target_type is not None:
        _validate_node_target(target_type, field="DjangoNodesField")
    _node_fields_declared.append("DjangoNodesField")

    def _resolve(
        root: Any,  # noqa: ARG001
        info: Info,
        # Raw strings for the same reason as ``DjangoNodeField``'s ``id``
        # argument (Revision 7 P1).
        ids: list[strawberry.ID],
    ) -> Any:
        if not ids:
            # Zero database access (spec Edge cases).
            return []
        # Decode every id BEFORE any query - a malformed id anywhere fails the
        # whole field (Decision 5 "Batch decode failures fail the whole field").
        decoded = [_decode_or_graphql_error(raw_id) for raw_id in ids]
        for resolved, _ in decoded:
            _check_typed_match(target_type, resolved)
        # Group coercible (type, pk) by decoded type - insertion-ordered, pks
        # in input order with duplicates preserved; uncoercible positions are
        # reserved null holes that never poison the batch ``pk__in``.
        groups: dict[type, list[Any]] = {}
        positions: list[tuple[type, int] | None] = []
        for resolved, node_id in decoded:
            pk = _coerce_pk_or_none(resolved, node_id)
            if pk is None:
                positions.append(None)
                continue
            pks = groups.setdefault(resolved, [])
            positions.append((resolved, len(pks)))
            pks.append(pk)
        if in_async_context():
            # ONE gathering coroutine; per-call dispatch because there is no
            # consumer resolver to inspect at construction (the deliberate
            # contrast with connection.py's committed-at-construction split).
            # Sequential awaits, not asyncio.gather - Django async-ORM
            # connection safety, and the spec requires only "a single
            # gathering coroutine".

            async def _gather() -> list[Any]:
                per_type: dict[type, list[Any]] = {}
                for resolved_type, pks in groups.items():
                    # ``resolve_nodes`` is AwaitableOrValue: the framework
                    # default returns a coroutine in async context, but a valid
                    # synchronous consumer override returns the list directly -
                    # await only when the result is actually awaitable, never
                    # unconditionally (spec-032 feedback P1).
                    result = resolved_type.resolve_nodes(info=info, node_ids=pks, required=False)
                    if inspect.isawaitable(result):
                        result = await result
                    per_type[resolved_type] = [
                        _stamp_node_type(resolved_type, node)
                        for node in _check_nodes_result(resolved_type, result, pks)
                    ]
                return _interleave(positions, per_type)

            return _gather()
        per_type = {
            resolved_type: [
                _stamp_node_type(resolved_type, node)
                for node in _check_nodes_result(
                    resolved_type,
                    resolved_type.resolve_nodes(info=info, node_ids=pks, required=False),
                    pks,
                )
            ]
            for resolved_type, pks in groups.items()
        }
        return _interleave(positions, per_type)

    return strawberry.field(
        resolver=_resolve,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
