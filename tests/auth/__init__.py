"""Package-internal tests for the opt-in auth subsystem (spec-040).

Holds ONLY the residue a live fakeshop ``/graphql/`` request cannot drive: the
surface-keyed declaration ledger / bind, register-rider factory cache and decode /
write defense-in-depth, ``current_user`` alias lifecycle, permission-gate variants
on isolated throwaway schemas (one-declaration-per-process vs the aggregate
AllowAny default), session-store failure injection, dispatch spies, and
Channels / WebSocket transport (no ``config/asgi.py``). Consumer-reachable
``login`` / ``logout`` / ``register`` / ``me`` behavior lives in
``examples/fakeshop/test_query/test_auth_api.py``.
"""
