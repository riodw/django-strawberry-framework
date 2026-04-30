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
"""

import logging
from typing import Any

from django.db.models import Prefetch  # noqa: F401  (used by Slice 6 implementation)
from strawberry.extensions import SchemaExtension

logger = logging.getLogger("django_strawberry_framework")


class DjangoOptimizerExtension(SchemaExtension):
    """Strawberry schema extension that optimizes Django querysets per request."""

    def resolve(
        self,
        _next: Any,
        root: Any,
        info: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Sync resolver wrapper that optimizes any returned ``QuerySet``.

        Algorithm (slice 4 implements steps 1–3; slice 5 adds 4; slice 6
        adds 5):

        1. Call ``_next(root, info, *args, **kwargs)`` to obtain the raw
           resolver result.
        2. If the result is not a ``QuerySet``, return it unchanged
           (mutations, scalars, computed fields, plain lists).
        3. Look up the resolver's GraphQL return type in ``registry``;
           if the model has no registered ``DjangoType`` we have no plan
           — log and return the queryset unchanged.
        4. Walk ``info.selected_fields`` to collect:

           - related fields (FK / OneToOne / reverse / M2M)
           - scalar fields (for ``only()`` projection)

        5. For each related field, call ``plan_relation`` to choose
           between ``select_related`` and ``Prefetch`` (downgrade rule
           applies when the target type has a custom ``get_queryset``).
        """
        result = _next(root, info, *args, **kwargs)
        # TODO(slice 4): if isinstance(result, QuerySet), look up the
        # return type's DjangoType in registry, walk info.selected_fields,
        # and apply select_related / prefetch_related per relation.
        # TODO(slice 5): apply only(...) projection of selected scalars.
        # TODO(slice 6): downgrade select_related to Prefetch when the
        # target type has a custom get_queryset (delegate via
        # plan_relation below).
        return result

    async def aresolve(
        self,
        _next: Any,
        root: Any,
        info: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Async resolver wrapper. Same algorithm as ``resolve``.

        Strawberry calls ``aresolve`` for async resolvers; the
        optimization itself is sync (querysets are lazy regardless of
        async vs. sync execution), so the async path is a thin wrapper
        that awaits ``_next`` and reuses the sync planning logic.
        """
        result = await _next(root, info, *args, **kwargs)
        # TODO(slice 4): factor the optimization core out of ``resolve``
        # into a private ``_optimize_queryset(qs, info)`` helper so this
        # method can call it without duplicating the walk.
        return result

    def plan_relation(
        self,
        field: Any,
        target_type: type,
        info: Any,
    ) -> tuple[str, Any]:
        """Plan a single relation traversal.

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
        # TODO(slice 6): implement per the algorithm above. Log every
        # downgrade decision via ``logger.debug`` so consumers can see
        # which relations the visibility rule rerouted to Prefetch.
        raise NotImplementedError("plan_relation pending Slice 6")
