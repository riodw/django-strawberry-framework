"""Tests for package Strawberry schema extensions.

Request-impossible ``DjangoDebugExtension`` mechanics live in this package;
real GraphQL HTTP behavior over fakeshop models belongs in
``examples/fakeshop/test_query/test_debug_extension_api.py`` (spec-044
Decision 11). Operation-state internals that no response can show live in
``test_operation_state.py``; their disclosure outcomes belong in
``test_extension_isolation_api.py``, ``test_resource_policy_api.py``, and
``test_error_policy_api.py``. No shared test helpers are exported here.
"""
