"""Package-internal tests for the planned auth subsystem."""

# TODO(spec-040 Slice 1-2): keep only non-live auth internals in this mirror
# package. Pseudocode: ledger/bind/cache/async/sessionless tests live here; any
# behavior reachable through a real fakeshop ``/graphql/`` request belongs in
# ``examples/fakeshop/test_query/test_auth_api.py`` instead.
