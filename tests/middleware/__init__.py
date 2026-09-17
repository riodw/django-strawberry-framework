"""Tests for package Django middleware integrations.

Toolbar-present GraphQL / panel / pass-through rows live in
``examples/fakeshop/test_query/test_debug_toolbar_api.py`` (fakeshop ships the
``debug_toolbar`` app, the package middleware, ``INTERNAL_IPS``, and
``debug_toolbar_urls()``). This package keeps import-guard, unreachable-bail,
and template-source rows no live request can express.
"""
