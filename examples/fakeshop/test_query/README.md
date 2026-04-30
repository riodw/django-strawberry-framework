# test_query

Live GraphQL-API tests for the **fakeshop** example project.

Tests in this directory exercise the full Django + Strawberry HTTP stack end-to-end by sending requests to `/graphql/` (typically via `django.test.Client.post(...)`). They are slower than the in-process schema tests under [`../tests/`](../tests/) but verify the entire request pipeline — URL routing, view, schema execution, and JSON response serialization.

Use the sibling [`../tests/`](../tests/) directory for tests that exercise schemas (via `schema.execute_sync`), services, models, admin, management commands, or URLs **without** hitting `/graphql/` over HTTP.

This directory is currently empty; live API tests will land here as the schema gains real types and resolvers.
