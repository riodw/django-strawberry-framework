"""Tests for package Django middleware integrations.

Middleware-specific tests live in this package, not in
``examples/fakeshop/test_query/``: fakeshop's shipped settings deliberately do
not install the optional toolbar app or middleware, so no live ``/graphql/``
request through the example's own configuration can reach these lines (the
live-first mandate's genuinely-unreachable fallback, spec-042 Decision 9).
"""
