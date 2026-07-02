"""Planned fakeshop GraphQL auth surface for spec-040.

The app is intentionally schema-only: it declares the example ``UserType`` and
the auth fields once the package factories exist, but it adds no models or
services. Live behavior belongs in ``examples/fakeshop/test_query/test_auth_api.py``.
"""

# TODO(spec-040 Slice 1): add the fakeshop user type and login/logout fields.
# Pseudocode: declare ``UserType`` over ``get_user_model()`` with fields
# ``("id", "username", "email")`` and ``relay.Node``, then expose
# ``login_mutation()`` and ``logout_mutation()`` on this app's ``Mutation`` type.
# Keep ``password`` and privilege columns off ``UserType``; this type is the
# authenticated read surface for login/register/me.

# TODO(spec-040 Slice 2): extend the same surface with register/me. Pseudocode:
# add a ``Query.me`` field from ``current_user()`` and a ``Mutation.register``
# field from ``register_mutation()``.
# ``register`` must round-trip through the live suite: register -> login -> me ->
# logout, plus duplicate username and weak-password envelopes.
