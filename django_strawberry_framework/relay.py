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

The encode/decode internals stay in ``types/relay.py`` (spec-031 Decision 11
reserved this top-level module for the root fields).

Engine note (spec-032 Edge cases): Strawberry only registers schema types it
can reach. A schema whose *only* root field is the interface-typed bare
``node`` must pass its concrete types explicitly via
``strawberry.Schema(types=[...])`` or expose them through other fields - this
is engine behavior, not package-fixable.
"""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Any

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError
from strawberry.types import Info
from strawberry.utils.inspect import in_async_context

from .exceptions import ConfigurationError
from .list_field import _validate_djangotype_target
from .types.base import _is_relay_shaped
from .types.relay import _model_for, decode_global_id

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
    """Coerce ``node_id`` to the target's pk Python type; ``None`` if uncoercible.

    ``decode_global_id`` validates payload SHAPE only, so a well-formed
    ``library.genre:abc`` decodes to ``(GenreType, "abc")``; a raw
    ``qs.filter(pk="abc")`` would leak Django's ``ValueError: Field 'id'
    expected a number``. A coercion failure is treated as "identifies no
    row" -> ``null`` (single) / positional ``null`` hole (batch), with no
    query issued, so the no-existence-oracle property is unaffected
    (Decision 5, Revision 7 P2).
    """
    try:
        return _model_for(resolved_type)._meta.pk.to_python(node_id)
    except (ValueError, ValidationError):
        return None


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


def _validate_node_target(target_type: type, *, field: str) -> None:
    """Run the four shared target guards plus the Relay-Node-shaped fifth guard.

    The shared four come from ``list_field.py::_validate_djangotype_target``
    (no ``resolver=`` seam exists on a refetch field, so ``None`` is passed).
    The fifth reuses ``types/base.py::_is_relay_shaped`` exactly as
    ``connection.py::DjangoConnectionField`` does - including its
    construction-time-tuple rationale (a Meta-declared ``relay.Node`` is in
    ``definition.interfaces`` before Phase 2.5 injects it into ``__bases__``).
    """
    _validate_djangotype_target(target_type, None, field=field)
    definition = target_type.__django_strawberry_definition__
    if not _is_relay_shaped(target_type, definition.interfaces):
        raise ConfigurationError(
            f"{field} requires a Relay-Node-shaped DjangoType target; add "
            "`relay.Node` to `Meta.interfaces` (or inherit `relay.Node` directly)",
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
    """
    return [
        None if position is None else per_type_results[position[0]][position[1]]
        for position in positions
    ]


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
        # Pass-through: in async context ``resolve_node`` returns a coroutine
        # Strawberry's executor awaits as a plain-field return (Edge cases
        # "Async end-to-end"). Calling the classmethod (not the underscore
        # default) preserves consumer overrides for free.
        return resolved.resolve_node(pk, info=info, required=False)

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
                    per_type[resolved_type] = result
                return _interleave(positions, per_type)

            return _gather()
        per_type = {
            resolved_type: resolved_type.resolve_nodes(info=info, node_ids=pks, required=False)
            for resolved_type, pks in groups.items()
        }
        return _interleave(positions, per_type)

    return strawberry.field(
        resolver=_resolve,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
