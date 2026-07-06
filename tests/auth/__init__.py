"""Package-internal tests for the opt-in auth subsystem (spec-040).

Holds ONLY the non-live auth internals the one-declaration-per-process rule makes
unreachable through a real fakeshop ``/graphql/`` request: the surface-keyed
declaration ledger / bind, the register rider's factory cache + password-hash write
step (plaintext-never-persisted on both the sync and async paths), the
``current_user`` alias lifecycle + resolver, the permission-gate variants (exact
denial strings on isolated throwaway schemas), and the async / sessionless edges.
Any behavior a live request can drive belongs in
``examples/fakeshop/test_query/test_auth_api.py`` instead.
"""
