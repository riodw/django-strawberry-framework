"""Project-level GraphQL schema that composes every fakeshop app query.

The module imports the per-app ``Query`` types, finalizes all collected
``DjangoType`` classes, and exposes the top-level ``schema`` served by
``config.urls``.

This mirrors the ``cookbook/schema.py`` layout from the
``django-graphene-filters`` example, adapted to Strawberry.  The
graphene-only ``DjangoDebug`` field has no direct Strawberry analogue
and is left out for now.
"""

import strawberry
from apps.glossary.schema import Query as GlossaryQuery
from apps.kanban.schema import Query as KanbanQuery
from apps.library.schema import Query as LibraryQuery
from apps.products.schema import Query as ProductsQuery
from apps.scalars.schema import Query as ScalarsQuery

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    finalize_django_types,
    strawberry_config,
)


@strawberry.type
class Query(LibraryQuery, ProductsQuery, ScalarsQuery, KanbanQuery, GlossaryQuery):
    """Top-level Query - extends each app's Query."""


# TODO(spec-036 Slice 4): compose the products Mutation into the project schema.
# Pseudocode:
# - import ``Mutation as ProductsMutation`` from ``apps.products.schema``;
# - declare a top-level Strawberry ``Mutation`` class that extends it;
# - pass ``mutation=Mutation`` into ``strawberry.Schema`` below;
# - keep finalization before Schema construction so mutation payload lazy refs
#   resolve after phase-2.5 binding.
finalize_django_types()

# Module-level singleton wrapped in a factory: ``get_extensions`` runs the
# callable per request and gets the same ``_optimizer`` back, so the
# instance-bound plan cache is preserved, and because the entry is a callable
# (not an instance) ``Schema.__init__`` emits no deprecation warning.
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
