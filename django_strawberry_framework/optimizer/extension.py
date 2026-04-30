"""``DjangoOptimizerExtension`` — Strawberry schema extension solving N+1.

Opt-in at schema construction::

    schema = strawberry.Schema(
        query=Query,
        extensions=[DjangoOptimizerExtension()],
    )

The extension wraps each resolver via Strawberry's ``resolve`` /
``aresolve`` hooks. When a resolver returns a ``QuerySet``, the extension
walks ``info.selected_fields`` to determine which related fields and
scalars are selected, looks up each return type in the registry, and
applies ``select_related`` / ``prefetch_related`` / ``only()`` to the
queryset before passing it back to Strawberry's machinery.

Load-bearing rule: when a related field's target ``DjangoType`` defines a
non-default ``get_queryset``, generate a ``Prefetch(...)`` keyed on the
filtered queryset instead of a ``select_related``. This is the
visibility-leak fix from strawberry-graphql-django #572 / #583. We copy
the behaviour, not the API.

Status: this module currently ships the depth-1 per-resolver cardinality
dispatch from ``spec-django_types.md`` Slice 4 (``resolve`` / ``aresolve``
hooks, ``_plan``, ``_unwrap_return_type``, ``_snake_case``). Slices O1
through O6 in ``docs/spec-optimizer.md`` rebuild it on a top-level
selection-tree-walk architecture: O3 replaces the per-resolver hooks
with ``on_executing_start`` so nested prefetch chains plan in a single
pass; O2 promotes ``_plan`` to a pure ``optimizer/walker.py`` module;
O4 emits nested chains (``items__entries``); O5 adds ``only()``
projection (with FK-column inclusion); O6 lands the ``Prefetch``
downgrade for visibility-aware target types. O1 is a separate seam in
``DjangoType.__init_subclass__`` — custom resolvers per relation field —
because the default ``getattr`` resolver chokes on Django's
``RelatedManager``.
"""

import logging
from typing import Any, get_args, get_origin

from django.db import models
from strawberry.extensions import SchemaExtension

from .registry import registry

logger = logging.getLogger("django_strawberry_framework")


class DjangoOptimizerExtension(SchemaExtension):
    """Strawberry schema extension that optimizes Django querysets per request.

    Current state (Slice 4): depth-1 per-resolver dispatch on cardinality
    flags. ``spec-optimizer.md`` slices O1-O6 rebuild this on the
    selection-tree-walk architecture; see the module docstring for the
    slice ordering.
    """

    # TODO(spec-optimizer.md O3): replace ``resolve`` and ``aresolve``
    # below with ``on_executing_start`` so the planner runs once at the
    # top of execution. Per-resolver hooks cannot emit nested prefetch
    # chains because the outer queryset is already evaluated by the
    # time inner resolvers fire. The rewrite walks the entire selection
    # tree once and applies the plan to the root queryset before
    # evaluation. Confirm at implementation time that
    # ``info.selected_fields`` is available at the new hook; if not,
    # fall back to ``resolve`` on the root only, gated by
    # ``info.path.prev is None``.

    def resolve(
        self,
        _next: Any,
        root: Any,
        info: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Sync resolver wrapper that optimizes any returned ``QuerySet``."""
        return self._optimize(_next(root, info, *args, **kwargs), info)

    async def aresolve(
        self,
        _next: Any,
        root: Any,
        info: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Async resolver wrapper. Awaits ``_next`` then reuses the sync planner."""
        return self._optimize(await _next(root, info, *args, **kwargs), info)

    def _optimize(self, result: Any, info: Any) -> Any:
        """Core optimizer. Shared by ``resolve`` and ``aresolve``.

        Algorithm (Slice 4 shipped steps 1–4; ``spec-optimizer.md`` O5
        adds ``only()`` (step 5); O6 replaces step 4 with
        ``plan_relation``):

        1. If the resolver returned anything other than a ``QuerySet``
           (mutations, scalars, plain lists), pass through unchanged.
        2. Walk wrapper types (``list[T]``, Strawberry ``of_type``) to
           reach the underlying ``DjangoType`` class.
        3. Reverse-lookup the Django model via ``registry.model_for_type``.
           Unregistered types fall through to no-op (we have no plan).
        4. Plan ``select_related`` / ``prefetch_related`` per selected
           relation using the cardinality flags on Django's field meta.
        """
        if not isinstance(result, models.QuerySet):
            return result
        target_type = self._unwrap_return_type(info.return_type)
        target_model = registry.model_for_type(target_type)
        if target_model is None:
            logger.debug(
                "Optimizer: %s has no registered DjangoType; passing queryset through unchanged.",
                target_type,
            )
            return result
        selects, prefetches = self._plan(info, target_model)
        if selects:
            result = result.select_related(*selects)
        if prefetches:
            result = result.prefetch_related(*prefetches)
        return result

    def _unwrap_return_type(self, rt: Any) -> Any:
        """Unwrap one layer of list / Strawberry-list-wrapper around the inner type.

        Strawberry exposes lists either as native ``typing.list[T]`` or
        wraps them in an internal ``StrawberryList``-style object that
        carries an ``of_type`` attribute. Handling both styles keeps the
        extension portable across Strawberry versions.
        """
        inner = getattr(rt, "of_type", None)
        if inner is not None:
            return inner
        if get_origin(rt) is list:
            return get_args(rt)[0]
        return rt

    def _plan(
        self,
        info: Any,
        model: type[models.Model],
    ) -> tuple[list[str], list[str]]:
        """Plan ``select_related`` / ``prefetch_related`` lists for the resolver.

        Walks ``info.selected_fields[0].selections`` (the GraphQL
        children of the current resolver), maps each selected name back
        to a Django field via snake_case conversion + ``model._meta``
        lookup, and routes each relation to the appropriate optimizer
        method based on cardinality. Single-side relations (forward FK,
        forward OneToOne) become ``select_related``; many-side relations
        (M2M, reverse FK / OneToOne) become ``prefetch_related``.
        """
        # TODO(spec-optimizer.md O2): extract this method into a new
        # ``optimizer/walker.py`` module exposing
        # ``plan_optimizations(info, model) -> OptimizationPlan``. Make
        # it a pure function so the walk is unit-testable in isolation
        # against synthetic ``info`` objects without Strawberry
        # execution. The current implementation is the depth-1 ancestor
        # of that walker.
        # TODO(spec-optimizer.md O4): once O2's walker exists, extend it
        # to emit nested-relation chains like
        # ``prefetch_related("items__entries")`` rather than the flat
        # single-level prefetches this implementation produces. Tests
        # assert query counts at depths 2 and 3 (``category > items >
        # entries`` and ``entry > item > category``).
        # TODO(spec-optimizer.md O5): extend the O2 walker to emit
        # ``only()`` column projections, including the FK columns
        # required to materialize ``select_related`` joins (per
        # ``spec-django_types.md`` "only() and FK columns"). Verify via
        # ``qs.query.deferred_loading`` in tests.
        if not info.selected_fields:
            return [], []
        sel_root = info.selected_fields[0].selections
        selects: list[str] = []
        prefetches: list[str] = []
        field_map = {f.name: f for f in model._meta.get_fields()}
        for sel in sel_root:
            python_name = self._snake_case(sel.name)
            django_field = field_map.get(python_name)
            if django_field is None or not django_field.is_relation:
                continue
            if django_field.many_to_many or django_field.one_to_many:
                prefetches.append(python_name)
            else:
                selects.append(python_name)
        return selects, prefetches

    @staticmethod
    def _snake_case(name: str) -> str:
        """Convert a Strawberry default-cased GraphQL name back to ``snake_case``.

        Strawberry's default name converter emits ``camelCase`` from
        ``snake_case`` Python attributes; reversing it lets us look up
        the corresponding Django field name without an extra mapping.
        """
        out: list[str] = []
        for i, c in enumerate(name):
            if i > 0 and c.isupper():
                out.append("_")
            out.append(c.lower())
        return "".join(out)

    def plan_relation(
        self,
        field: Any,
        target_type: type,
        info: Any,
    ) -> tuple[str, Any]:
        """Plan a single relation traversal (Slice 6 entry point).

        Returns ``("select", field_name)`` or
        ``("prefetch", Prefetch(...))`` describing how the optimizer
        should materialize this relation on the parent queryset.

        Algorithm (per the spec's "N+1 strategy" section):

        1. Build the target queryset:
           ``field.related_model.objects.all()``.
        2. Apply ``target_type.get_queryset(target_qs, info)`` so
           visibility filters take effect.
        3. If the relation is many-side (``many_to_many`` or
           ``one_to_many``), emit ``("prefetch", Prefetch(field.name,
           queryset=target_qs))``.
        4. Otherwise, if ``target_type.has_custom_get_queryset()`` is
           true, downgrade to ``("prefetch", Prefetch(field.name,
           queryset=target_qs))`` so the visibility filter applies
           across the join.
        5. Otherwise, emit ``("select", field.name)`` for a plain
           ``select_related``.
        """
        # TODO(spec-optimizer.md O6): implement per the algorithm
        # above. Log every downgrade decision via ``logger.debug`` so
        # consumers can see which relations the visibility rule
        # rerouted to Prefetch. O6 also wires this into the O2 walker
        # so the planner delegates to ``plan_relation`` per relation
        # rather than dispatching on cardinality directly.
        raise NotImplementedError("plan_relation pending spec-optimizer.md O6")
