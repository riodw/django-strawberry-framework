"""Planned live sync-HTTP contract for ``DjangoListField`` arguments (spec-050 Slice 4).

This is the SYNC counterpart of ``test_list_field_async_api.py``. The rows live
here rather than in ``test_library_api.py`` because that module is the broad
library APPLICATION suite - relation traversal, enums, optimizer SQL shape, the
filter/order surfaces, the row-preserving predicate oracle - and folding a field
factory's whole argument matrix into it would bury the feature. The live-tier
guide permits cross-cutting suites; this module uses the same already-registered
library types and the same inline library-model creation, so the split costs no
fixtures.

Shipped fakeshop SDL changes only through factory behavior on the three already
declared Branch list fields in ``apps/library/schema.py::Query``. No new root
field is added to the shipped schema: exceptional source shapes and custom name
converters are holder-mounted in test-local schemas only.
"""

# TODO(spec-050 slice 4): Replace this planning-only module with the sync live
# suite after Slices 1-3 land. Use only already-registered fakeshop DjangoTypes;
# a throwaway DjangoType would mutate the registry and fail the acceptance
# conftest's registration identity guard. Create Branch / Shelf / library users
# inline with ``Model.objects.create(...)`` / ``create_user(...)``; a genuinely
# mixed row that also creates products models begins with ``seed_data(N)``.
#
# Pseudocode - the shipped-field surface:
#
# - Introspect ``allLibraryBranchesViaListField`` and its nullable and
#   manager-resolver siblings: nullable ``Int`` offset, nullable ``Int`` limit,
#   and the existing Branch order input, with return shapes unchanged.
# - Staff context: ``orderBy: [{name: ASC}, {id: ASC}], offset: 1, limit: 2``
#   returns the second and third VISIBLE rows in that exact order. Anonymous
#   context orders by the unguarded ``city`` then ``id`` and proves a restricted
#   Branch is removed by ``get_queryset`` BEFORE the offset is counted.
# - Offset ALONE, limit omitted, returns ``[offset:offset + effective_ceiling]``
#   with the raised low mark and the unchanged policy high mark in captured SQL.
# - Negative and over-ceiling offset and limit return the package extensions;
#   two numeric failures in one request report ``offset`` first.
# - Coercion failures (string, bool, out-of-range int, non-integral/non-finite
#   float variables, float literals) are GraphQL ``Int`` errors performing no
#   resolver SQL, while an integral float variable coerces and executes.
# - ``limit: 0`` returns an empty list with no row-fetch query; ``offset: 1,
#   limit: 0`` still obeys the order precondition.
# - Two ALIASES of the same field with different windows return independent
#   pages: root list fields share no window state and no merged plan.
#
# Pseudocode - the order precondition, both verdicts:
#
# - Nonzero offset with no order returns ``LIST_ARGUMENT_INVALID`` /
#   ``order_required``; empty and all-null order input do not satisfy it.
# - A holder-mounted field over a registered type whose model declares stable
#   non-random ``Meta.ordering`` accepts nonzero offset with NO ``orderBy`` and
#   no injected pk term; a sibling whose resolver calls ``.order_by()`` clears
#   that default and flips the identical request to ``order_required``.
# - A holder-mounted field over a type with NEITHER ``Meta.orderset_class`` NOR
#   model default ordering publishes offset/limit and no ``orderBy``, and every
#   positive offset on it is rejected - the permanently-unusable coordinate the
#   spec accepts, proven rather than conceded.
# - Anonymous staff-gated ``name`` order plus nonzero offset returns the ORDER
#   PERMISSION denial first, pinning permission-before-offset precedence.
# - A to-many aggregate order through ``shelves`` plus limit/offset returns one
#   row per Branch, with one ``LIMIT/OFFSET`` pair and no ``DISTINCT`` in SQL.
#
# Pseudocode - exceptional source shapes (holder-mounted only):
#
# - ``branches_materialized`` / ``branches_nullable_none`` / ``branches_presliced``
#   / ``branches_trusted`` / ``branches_combined``. Non-queryset sources take
#   limit and zero offset; any non-null ``orderBy`` (including ``[]``) returns
#   ``queryset_required`` and nonzero offset returns ``order_required``.
# - Nullable AND non-null outer annotations over the same None-returning source:
#   both preserve ``null`` under limit-only and both error under a rejected
#   argument, propagating through the declared nullability. This is capability
#   validation deliberately outranking nullable-result propagation.
# - ``branches_presliced`` keeps the shared visibility boundary's actionable
#   ConfigurationError under the error-policy pass-through fixture, for omitted
#   AND active arguments alike.
# - ``branches_combined``'s omitted/all-null branch is asserted against a NAMED
#   BASELINE HELPER capturing the pre-card result-or-error, its SQL, and its
#   ``get_queryset`` call count. "Not the new rejection" is NOT a sufficient
#   oracle: a combined Branch queryset also meets ``BranchType.get_queryset``
#   filtering and may legitimately produce data or a pre-existing error. Every
#   non-null argument, zero and empty values included, rejects at the source
#   seal before the hook, OrderSet permission, or windowing; a hook-returned
#   combination rejects at the result seal.
#
# Pseudocode - OrderSet overrides and naming:
#
# - A conforming test-local override proves public dispatch, and one returning a
#   sealable ``QuerySet`` SUBCLASS derived from its sealed input SUCCEEDS: the
#   seal normalizes a subclass into a plain queryset rather than rejecting it.
# - Malformed overrides returning sliced, evaluated, projection, combined,
#   wrong-model, non-queryset, sync-awaitable, async-method-non-awaitable, or
#   residual-async-awaitable results prove post-apply ConfigurationError and
#   disposal. Wrong-route overrides live in test_multi_db.py under
#   FAKESHOP_SHARDED=1, covering the unrouted/hint-mismatch case as well as
#   ``.using("default")`` versus ``.using("shard_b")``.
# - ``strawberry_config(auto_camel_case=False)`` and a custom NameConverter
#   schema prove SDL/query spelling and ``ListArgumentError.argument`` follow the
#   ACTIVE converter for all three Python parameters, never a hard-coded literal.
#
# Pseudocode - isolation and generated bookkeeping:
#
# - Every test-local mount uses the module-level current-schema holder under
#   ``override_settings(ROOT_URLCONF=__name__)`` and resets that holder plus
#   Django's URL caches in ``finally``, under the shared schema_reload.py
#   discipline.
# - Once this path is in the git index, run the tracked-path constants builder;
#   do not hand-edit ``apps/kanban/constants.py``. Regenerate ``docs/TREE.md`` in
#   Slice 5 and add this module to the live-tier README's suite enumeration.
