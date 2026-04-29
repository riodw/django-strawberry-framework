"""Project-level GraphQL schema.

Composes the per-app ``Query`` types into the top-level ``schema``
served by ``urls.py``.

This mirrors the ``cookbook/schema.py`` layout from the
``django-graphene-filters`` example, adapted to Strawberry.  The
graphene-only ``DjangoDebug`` field has no direct Strawberry analogue
and is left out for now.
"""

import strawberry
from fakeshop.products.schema import Query as ProductsQuery


@strawberry.type
class Query(ProductsQuery):
    """Top-level Query — extends each app's Query."""


schema = strawberry.Schema(query=Query)
