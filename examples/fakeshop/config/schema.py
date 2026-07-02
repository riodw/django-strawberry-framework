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
from apps.accounts.schema import Mutation as AccountsMutation
from apps.accounts.schema import Query as AccountsQuery
from apps.glossary.schema import Query as GlossaryQuery
from apps.kanban.schema import Query as KanbanQuery
from apps.library.schema import Mutation as LibraryMutation
from apps.library.schema import Query as LibraryQuery
from apps.products.schema import Mutation as ProductsMutation
from apps.products.schema import Query as ProductsQuery
from apps.scalars.schema import Mutation as ScalarsMutation
from apps.scalars.schema import Query as ScalarsQuery

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    finalize_django_types,
    strawberry_config,
)


@strawberry.type
class Query(LibraryQuery, ProductsQuery, ScalarsQuery, KanbanQuery, GlossaryQuery, AccountsQuery):
    """Top-level Query - extends each app's Query."""


@strawberry.type
class Mutation(ProductsMutation, ScalarsMutation, LibraryMutation, AccountsMutation):
    """Top-level Mutation - extends each app's Mutation.

    Products carries the create/update/delete write surface (spec-036 Slice 4);
    the scalars app adds the file-backed ``createMediaSpecimen`` so the spec-037
    ``Upload`` mutation-input mapping is exercised over a live multipart
    ``/graphql/`` request; the library app adds the raw-pk relation form/model
    mutations (``Shelf`` relations target the non-Relay ``BranchType``) so the
    raw-pk relation visibility + ``to_field_name`` branches are earned over a live
    request (spec-038 / the ``test_query`` live-coverage rule); the accounts app
    adds the spec-040 session-auth surface (``login`` / ``logout`` / ``register``,
    plus the ``me`` query) at the AllowAny default. The mutation
    phase-2.5 bind runs inside ``finalize_django_types()`` below, so the
    ``DjangoMutationField`` lazy payload / ``data:`` refs resolve at ``Schema(...)``
    build.
    """


# Finalization must precede ``strawberry.Schema(...)``: phase 2.5 materializes the
# ``<Model>Input`` / ``<Model>PartialInput`` / ``<Name>Payload`` classes (and binds
# the mutation fields) before the schema build resolves their lazy references.
finalize_django_types()

# Module-level singleton wrapped in a factory: ``get_extensions`` runs the
# callable per request and gets the same ``_optimizer`` back, so the
# instance-bound plan cache is preserved, and because the entry is a callable
# (not an instance) ``Schema.__init__`` emits no deprecation warning.
_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
