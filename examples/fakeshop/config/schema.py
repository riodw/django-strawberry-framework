"""Project-level GraphQL schema.

Composes the per-app ``Query`` types into the top-level ``schema``
served by ``config.urls``.

This mirrors the ``cookbook/schema.py`` layout from the
``django-graphene-filters`` example, adapted to Strawberry.  The
graphene-only ``DjangoDebug`` field has no direct Strawberry analogue
and is left out for now.
"""

import strawberry
from apps.library.schema import Query as LibraryQuery
from apps.products.schema import Query as ProductsQuery

from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types


@strawberry.type
class Query(LibraryQuery, ProductsQuery):
    """Top-level Query — extends each app's Query."""


finalize_django_types()

schema = strawberry.Schema(
    query=Query,
    extensions=[DjangoOptimizerExtension()],
)
