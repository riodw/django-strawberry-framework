"""``DjangoOptimizerExtension`` — Strawberry schema extension solving N+1.

Opt-in at schema construction::

    schema = strawberry.Schema(
        query=Query,
        extensions=[DjangoOptimizerExtension()],
    )

The extension hooks Strawberry's ``resolve`` middleware. At the
operation's **root resolver** (detected via ``info.path.prev is None``)
it walks the entire selection tree once using the O2 walker, builds an
``OptimizationPlan``, and applies ``select_related`` /
``prefetch_related`` to the root queryset. Non-root resolvers pass
through untouched — Django's ``prefetch_related`` with ``__``-chained
paths handles nested optimization in a single pass.

Load-bearing rule (O6, not yet shipped): when a related field's target
``DjangoType`` defines a non-default ``get_queryset``, generate a
``Prefetch(...)`` keyed on the filtered queryset instead of a
``select_related``. This is the visibility-leak fix from
strawberry-graphql-django #572 / #583. We copy the behaviour, not the
API.

Architecture modeled on ``strawberry_django/optimizer.py`` — same
root-gate pattern, same ``ContextVar`` lifecycle, same recursive
type-tracing through graphql-core wrappers.
"""

import inspect
import logging
from contextvars import ContextVar
from typing import Any

from django.db import models
from strawberry.extensions import SchemaExtension

from ..registry import registry
from .walker import plan_optimizations

logger = logging.getLogger("django_strawberry_framework")

_optimizer_active: ContextVar[bool] = ContextVar(
    "django_strawberry_framework_optimizer_active",
    default=False,
)


def _resolve_model_from_return_type(info: Any) -> type[models.Model] | None:
    """Trace ``info.return_type`` through graphql-core wrappers to a Django model.

    graphql-core wraps resolver return types in layers of
    ``GraphQLNonNull`` and ``GraphQLList``. This function recursively
    peels ``.of_type`` until it reaches a leaf carrying a ``.name``
    attribute (a ``GraphQLObjectType``), then looks up the corresponding
    Strawberry type definition via the schema and reverse-maps to the
    Django model through the registry.

    Returns ``None`` when any step fails (unregistered type, non-object
    leaf, missing schema backref). The caller treats ``None`` as
    "nothing to optimize" and passes the queryset through unchanged.
    """
    rt = info.return_type
    while hasattr(rt, "of_type"):
        rt = rt.of_type
    type_name = getattr(rt, "name", None)
    if type_name is None:
        return None
    strawberry_schema = getattr(
        getattr(info, "schema", None),
        "_strawberry_schema",
        None,
    )
    if strawberry_schema is None:
        return None
    definition = strawberry_schema.get_type_by_name(type_name)
    if definition is None:
        return None
    origin = getattr(definition, "origin", None)
    return registry.model_for_type(origin)


class DjangoOptimizerExtension(SchemaExtension):
    """Strawberry schema extension that optimizes Django querysets per request.

    Hooks:

    - ``on_execute`` — sets a ``ContextVar`` marking the optimizer as
      active for the operation's lifetime.
    - ``resolve`` — gates on ``info.path.prev is None`` (root resolver
      only). Calls ``_next``, checks ``isinstance(QuerySet)``, traces
      the Django model from the graphql-core return type, runs the O2
      walker, applies the plan.
    """

    def on_execute(self) -> Any:  # type: ignore[override]
        """Mark the optimizer as active for the duration of execution."""
        token = _optimizer_active.set(True)
        yield
        _optimizer_active.reset(token)

    def resolve(
        self,
        _next: Any,
        root: Any,
        info: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Root-gated resolver hook.

        Only root-level resolvers (``info.path.prev is None``) trigger
        the optimization pass. All other resolvers pass through
        unchanged — the prefetch chain applied at the root handles
        nested relations via Django's ``__``-chain support.

        Handles both sync and async resolvers: when ``_next`` returns a
        coroutine (async resolver), returns an async wrapper that awaits
        the result before running ``_optimize``. Strawberry's
        ``SchemaExtension.resolve`` returns ``AwaitableOrValue`` for
        exactly this reason.
        """
        result = _next(root, info, *args, **kwargs)
        if info.path.prev is not None:
            return result
        if inspect.isawaitable(result):

            async def _async_optimize() -> Any:
                return self._optimize(await result, info)

            return _async_optimize()
        return self._optimize(result, info)

    def _optimize(self, result: Any, info: Any) -> Any:
        """Apply the O2 walker's plan to a root-level ``QuerySet``.

        Steps:

        1. Non-``QuerySet`` results pass through unchanged.
        2. Trace the graphql-core return type to a Django model.
        3. Run the O2 walker to build an ``OptimizationPlan``.
        4. Apply the plan to the queryset.
        """
        if not isinstance(result, models.QuerySet):
            return result
        target_model = _resolve_model_from_return_type(info)
        if target_model is None:
            logger.debug(
                "Optimizer: return type for %s has no registered DjangoType; "
                "passing queryset through unchanged.",
                info.field_name,
            )
            return result
        if not info.field_nodes:
            return result
        # Strawberry's Info.selected_fields peels from field_nodes;
        # at the raw GraphQLResolveInfo level we use the walker's
        # convert_selections to get the same shape, or we can access
        # the selections directly from the field node's selection set.
        # The O2 walker expects the children of the root field, so we
        # build the Strawberry-shaped selection list from field_nodes.
        from strawberry.types.nodes import convert_selections

        selections = convert_selections(info, info.field_nodes)
        # selections[0] is the root field; its .selections are the
        # children the walker needs.
        plan = plan_optimizations(selections[0].selections, target_model)
        if plan.is_empty:
            return result
        return plan.apply(result)

    def plan_relation(
        self,
        field: Any,
        target_type: type,
        info: Any,
    ) -> tuple[str, Any]:
        """Plan a single relation traversal (O6 entry point).

        Returns ``("select", field_name)`` or
        ``("prefetch", Prefetch(...))`` describing how the optimizer
        should materialize this relation on the parent queryset.
        """
        # TODO(spec-optimizer.md O6): implement. Log every downgrade
        # decision via ``logger.debug``. Wire into the O2 walker so
        # the planner delegates to ``plan_relation`` per relation
        # rather than dispatching on cardinality directly.
        raise NotImplementedError("plan_relation pending spec-optimizer.md O6")
