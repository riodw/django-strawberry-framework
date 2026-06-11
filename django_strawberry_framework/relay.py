"""Root Relay refetch fields - ``DjangoNodeField`` / ``DjangoNodesField``.

Staged home for ``WIP-ALPHA-032-0.0.9`` Slice 2 (``docs/spec-032-full_relay-0_0_9.md``
Decisions 3/4/5/11): the consumer-facing root ``node(id:)`` / ``nodes(ids:)``
factory functions. The encode/decode internals STAY in ``types/relay.py``
(spec-031 Decision 11 reserved this top-level module for the root fields);
this module will import ``decode_global_id`` from there.

The module is deliberately statement-free until Slice 2 lands: nothing imports
it yet, and ``fail_under = 100`` would flag any unexecuted stub line. The
Slice-2 change replaces the staged pseudocode below with the real factories and
removes every ``TODO(spec-032-full_relay-0_0_9 ...)`` anchor in the same change
(the ``AGENTS.md`` design-doc anchor discipline).
"""

# TODO(spec-032-full_relay-0_0_9 Slice 2): Module-level ledger backing the
# finalize-time no-Node-types check (Decision 8; the
# ``_helper_referenced_filtersets`` precedent - ``registry.clear()`` co-clears):
#   _node_fields_declared: list[str] = []  # noqa: ERA001

# TODO(spec-032-full_relay-0_0_9 Slice 2): Shared decode boundary (Decision 5).
# Every ConfigurationError from ``types/relay.py::decode_global_id`` (malformed
# base64, non-`type:id` payload, unresolvable label/name, strategy-forbidden
# shape, no recorded strategy) converts to the wire error - decode runs on
# payload data only, BEFORE any query, so nothing leaks row existence:
#   def _decode_or_graphql_error(gid):
#       try:  # noqa: ERA001
#           return decode_global_id(gid)  # noqa: ERA001
#       except ConfigurationError as exc:  # noqa: ERA001
#           raise GraphQLError(
#               f"Invalid GlobalID: {exc}",  # noqa: ERA001
#               extensions={"code": "GLOBALID_INVALID"},  # noqa: ERA001
#           ) from exc

# TODO(spec-032-full_relay-0_0_9 Slice 2): The single-node factory (bare +
# typed forms, Decision 4). Returns a ``strawberry.field(resolver=...)`` value
# picked up by Strawberry's class-body walk (the ``DjangoListField``
# mechanism); the consumer's class-attribute annotation drives the rendered
# SDL type, but resolution is nullable-by-contract: ``required=False``
# UNCONDITIONALLY, so the optional annotation spelling is the supported shape
# (Decision 5 / Revision 2 P2).
#   def DjangoNodeField(target_type=None, *, description=None,
#                       deprecation_reason=None, directives=()):
#       if target_type is not None:  # typed form
#           _validate_djangotype_target(target_type, None, field=...)  # noqa: ERA001
#           require _is_relay_shaped(target_type, definition.interfaces)
#       _node_fields_declared.append("DjangoNodeField")  # noqa: ERA001
#       def _resolve(root, info, id: relay.GlobalID):
#           resolved, node_id = _decode_or_graphql_error(id)  # noqa: ERA001
#           if target_type is not None and resolved is not target_type:
#               raise GraphQLError(<expected vs received type names>)
#           return resolved.resolve_node(node_id, info=info, required=False)  # noqa: ERA001
#           # Pass-through: a coroutine in async context is awaited as a
#           # plain-field return (Edge cases "Async end-to-end").
#       return strawberry.field(resolver=_resolve, description=..., ...)

# TODO(spec-032-full_relay-0_0_9 Slice 2): The batch factory (Decision 4).
# Same construction-time guards + ledger append as DjangoNodeField. Contract:
# input order preserved; positional ``null`` ONLY for well-formed-but-
# invisible/missing ids; a malformed id (or a wrong-type id under the typed
# form) ANYWHERE fails the WHOLE field - the ``[Node]!`` non-null nulls the
# enclosing ``data`` (Decision 5 "Batch decode failures fail the whole
# field"); duplicates resolve per position; one ``resolve_nodes`` call per
# distinct decoded type (Strawberry's ``get_node_list_resolver`` grouping,
# minus its index-map duplicate collapse - the reason the package owns this).
#   def DjangoNodesField(target_type=None, *, ...):
#       def _resolve(root, info, ids: list[relay.GlobalID]):
#           if not ids:
#               return []  # no database access  # noqa: ERA001
#           decoded = [_decode_or_graphql_error(g) for g in ids]  # noqa: ERA001
#           if target_type is not None:
#               reject any decoded type != target_type (whole field)
#           groups = group node_ids by decoded type, input order kept
#           if in_async_context():  # per-call dispatch (Edge cases) -
#               # NOT connection.py's commit-at-construction split: there
#               # is no consumer resolver to inspect at construction.
#               return _gather_async(groups)  # ONE gathering coroutine:  # noqa: ERA001
#               # awaits each type's resolve_nodes(...), then interleaves
#               # into input order with null holes.
#           per_type = {t: t.resolve_nodes(info=info, node_ids=nids,
#                       required=False) for t, nids in groups}
#           return interleave(per_type, input_positions)  # noqa: ERA001
#       return strawberry.field(resolver=_resolve, ...)
