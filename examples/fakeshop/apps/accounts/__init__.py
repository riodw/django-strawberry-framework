"""Schema-only accounts app exposing session-auth fields over Django's ``auth.User``.

It owns ``UserType`` plus login, logout, and register mutations and the ``me`` query
without introducing app models; live ``/graphql/`` coverage lives in
``test_query/test_auth_api.py``.
"""
