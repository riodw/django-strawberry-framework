"""Package-internal tests for the auth subsystem (spec-040).

Only non-live auth internals live in this mirror package - ledger / bind /
cache / async / sessionless mechanics plus the permission-gate variants that
cannot coexist with the aggregate fakeshop default surface. Any behavior
reachable through a real fakeshop ``/graphql/`` request is earned in
``examples/fakeshop/test_query/test_auth_api.py`` instead.
"""
