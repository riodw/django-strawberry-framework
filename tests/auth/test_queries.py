"""Package-internal tests for ``django_strawberry_framework/auth/queries.py`` (spec-040).

The ``current_user`` residue a live fakeshop request cannot drive: the
``CurrentUserAlias`` namespace lifecycle (the ``make_input_namespace`` trio +
its pre-bind ``register_subsystem_clear`` row), the injected-signature return
typing resolving to the concrete user type, the surface-keyed
current-user-only bind (its no-``UserType`` arm + no orphan payloads), the
permission-gate variants (denial string; gated-anonymous ``GraphQLError`` vs
the AllowAny ``null``), and the async lazy-user forcing inside the one
``sync_to_async`` boundary. The live ``me`` behavior (authenticated /
anonymous over ``/graphql/``) is earned in
``examples/fakeshop/test_query/test_auth_api.py``.
"""

from __future__ import annotations

import pytest
import strawberry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.utils.functional import SimpleLazyObject
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.auth import current_user, login_mutation
from django_strawberry_framework.auth import queries as auth_queries
from django_strawberry_framework.auth.queries import (
    CURRENT_USER_ALIAS_NAME,
    _current_user_alias_names,
    clear_current_user_alias_namespace,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.inputs import _materialized_names
from django_strawberry_framework.registry import iter_subsystem_clears, registry

User = get_user_model()


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry (co-clearing the auth declaration ledger) per test."""
    registry.clear()
    yield
    registry.clear()


class _IsAuthenticated:
    """An ``IsAuthenticated``-style gate: denies the anonymous caller."""

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        return instance is not None


def _declare_user_type():
    """Register a fresh Relay-backed primary ``DjangoType`` over the user model."""
    return type(
        "UserT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": User, "fields": ("id", "username", "email"), "primary": True},
            ),
        },
    )


def _session_request(user=None):
    request = RequestFactory().post("/graphql/")
    SessionMiddleware(lambda _request: None).process_request(request)
    request.user = user if user is not None else AnonymousUser()
    return request


def _me_schema(**current_user_kwargs) -> strawberry.Schema:
    """Declare UserT + a me-only Query; return the finalized schema."""
    _declare_user_type()

    @strawberry.type
    class Query:
        me = current_user(**current_user_kwargs)

    finalize_django_types()
    return strawberry.Schema(query=Query)


class _FakeConsumer:
    """The ``consumer`` half of Strawberry's ``ChannelsRequest`` duck shape."""

    def __init__(self, scope):
        self.scope = scope


class _FakeChannelsRequest:
    """A ``ChannelsRequest``-shaped object: ``consumer.scope`` + request attrs."""

    def __init__(self, scope):
        self.consumer = _FakeConsumer(scope)
        self.headers = {}
        self.method = "POST"


def _channels_context(scope):
    """A Strawberry-Channels mapping context (spec-041) that resolves to the adapter."""
    return {"request": _FakeChannelsRequest(scope)}


_ME_Q = "{ me { username } }"


def test_alias_namespace_rides_make_input_namespace_and_the_pre_bind_row():
    """The alias is a ``make_input_namespace``-owned emit artifact with a pre-bind row."""
    assert clear_current_user_alias_namespace in iter_subsystem_clears(before_bind=True)

    user_type = _declare_user_type()

    @strawberry.type
    class Query:
        me = current_user()

    finalize_django_types()
    # The bind pinned the resolved user primary as this module's parked global
    # (the ``strawberry.lazy`` target) through the trio's materializer.
    assert auth_queries.CurrentUserAlias is user_type
    assert _current_user_alias_names == {CURRENT_USER_ALIAS_NAME: user_type}


def test_injected_return_annotation_resolves_to_the_concrete_user_type():
    """The dispatcher's lazy return ref lands in the SDL as ``me: UserT`` (nullable)."""
    schema = _me_schema()
    assert "me: UserT" in str(schema)


def test_current_user_only_bind_emits_no_login_logout_payloads():
    """The surface-keyed bind: a me-only schema materializes the alias and nothing else."""
    _me_schema()
    assert "LoginPayload" not in _materialized_names
    assert "LogoutPayload" not in _materialized_names
    assert CURRENT_USER_ALIAS_NAME in _current_user_alias_names


def test_current_user_only_schema_without_user_type_raises_its_own_arm():
    """The current-user arm's auth-specific message, distinct from login's."""

    @strawberry.type
    class Query:
        me = current_user()

    with pytest.raises(
        ConfigurationError,
        match=r"auth current_user\(\) declared with no registered DjangoType for the user model",
    ):
        finalize_django_types()


def test_conflicting_current_user_gates_raise_the_one_declaration_error():
    current_user()
    with pytest.raises(ConfigurationError, match=r"auth current_user\(\) is already declared"):
        current_user(permission_classes=[_IsAuthenticated])


@pytest.mark.django_db
def test_allow_any_default_returns_null_for_anonymous_and_the_user_when_authenticated():
    """The two axes are distinct: allowed-but-anonymous is ``null``, never an error."""
    schema = _me_schema()
    anonymous = schema.execute_sync(_ME_Q, context_value=_session_request())
    assert anonymous.errors is None, anonymous.errors
    assert anonymous.data["me"] is None

    user = User.objects.create_user(username="me_probe", password="pw-9x-strong")
    authenticated = schema.execute_sync(_ME_Q, context_value=_session_request(user))
    assert authenticated.errors is None, authenticated.errors
    assert authenticated.data["me"] == {"username": "me_probe"}


@pytest.mark.django_db
def test_me_is_null_not_a_crash_when_the_request_user_is_absent():
    """An absent request user is anonymous -> ``null``, never a ``'NoneType'`` crash.

    ``request.user`` is ``None`` for a Strawberry-Channels
    ``ChannelsRequestAdapter`` whose scope carries no
    ``AuthMiddlewareStack``-populated user (spec-041's supported adapter shape;
    ``tests/utils/test_permissions.py`` pins ``.user`` -> ``None`` there), and
    absent entirely for a bare request wired without ``AuthenticationMiddleware``.
    Both must resolve ``me`` to ``null`` under the AllowAny default - the
    nullable-return contract is "not authenticated -> null", matching
    ``DjangoModelPermission.has_permission``'s ``getattr(request, "user", None)``
    / ``user is None`` guard. Pre-fix each path raised a top-level
    ``'NoneType' object has no attribute 'is_authenticated'``.
    """
    schema = _me_schema()

    # The Channels adapter shape: a mapping context whose scope has no ``user`` key,
    # so ``ChannelsRequestAdapter.user`` returns ``None``.
    channels = schema.execute_sync(
        _ME_Q,
        context_value=_channels_context({"type": "websocket"}),
    )
    assert channels.errors is None, channels.errors
    assert channels.data["me"] is None

    # A bare request that never had ``request.user`` set (no AuthenticationMiddleware).
    bare = RequestFactory().post("/graphql/")
    bare_res = schema.execute_sync(_ME_Q, context_value=bare)
    assert bare_res.errors is None, bare_res.errors
    assert bare_res.data["me"] is None


@pytest.mark.django_db
def test_gated_me_denies_the_anonymous_caller_with_the_exact_pinned_string():
    """An ``IsAuthenticated``-style gate turns anonymous ``null`` into the ``GraphQLError``."""
    schema = _me_schema(permission_classes=[_IsAuthenticated])
    denied = schema.execute_sync(_ME_Q, context_value=_session_request())
    assert denied.errors is not None
    assert denied.errors[0].message == "Not authorized to current_user UserT."

    user = User.objects.create_user(username="gated_probe", password="pw-9x-strong")
    allowed = schema.execute_sync(_ME_Q, context_value=_session_request(user))
    assert allowed.errors is None, allowed.errors
    assert allowed.data["me"] == {"username": "gated_probe"}


@pytest.mark.django_db(transaction=True)
async def test_async_gated_me_forces_the_lazy_user_inside_the_one_sync_boundary():
    """The gate's ``instance=request.user`` forces the ``SimpleLazyObject`` in-boundary.

    The Decision-10 async-gate fix: computing the gate argument forces the lazy
    user (a sync ORM touch that would raise ``SynchronousOnlyOperation`` outside
    a sync context); because the whole gate-then-return body runs inside the ONE
    ``sync_to_async(thread_sensitive=True)`` worker, the forced load succeeds and
    the recorded gate ``instance`` is the real user row.
    """
    seen = {}

    class RecordingGate:
        def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            seen.update(operation=operation, data=data, instance=instance)
            return True

    schema = _me_schema(permission_classes=[RecordingGate])
    user = await User.objects.acreate_user(username="lazy_probe", password="pw-9x-strong")

    request = RequestFactory().post("/graphql/")
    SessionMiddleware(lambda _request: None).process_request(request)
    # The middleware shape: a lazy user whose first attribute access hits the ORM.
    request.user = SimpleLazyObject(lambda: User.objects.get(username="lazy_probe"))

    res = await schema.execute(_ME_Q, context_value=request)
    assert res.errors is None, res.errors
    assert res.data["me"] == {"username": "lazy_probe"}
    assert seen["operation"] == "current_user"
    assert seen["data"] is None
    assert seen["instance"] == user


@pytest.mark.django_db
def test_me_composes_with_login_in_one_schema_without_visibility_rerun():
    """``me`` returns the actor even under a hide-everyone ``get_queryset`` (D-N1).

    A directory-shaped visibility hook that hides every row must not make ``me``
    (or the login node) return ``null`` for the logged-in actor - the two
    actor-returning surfaces deliberately skip the ``get_queryset`` re-run.
    """

    def _hide_everyone(cls, queryset, info, **kwargs):
        return queryset.none()

    type(
        "UserT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": User, "fields": ("id", "username", "email"), "primary": True},
            ),
            "get_queryset": classmethod(_hide_everyone),
        },
    )

    @strawberry.type
    class Query:
        me = current_user()

    @strawberry.type
    class Mutation:
        login = login_mutation()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, mutation=Mutation)

    User.objects.create_user(username="hidden_actor", password="pw-9x-strong")
    request = _session_request()
    login_res = schema.execute_sync(
        'mutation{ login(username: "hidden_actor", password: "pw-9x-strong"){ '
        "node{ username } errors{ field } } }",
        context_value=request,
    )
    assert login_res.errors is None, login_res.errors
    assert login_res.data["login"] == {"node": {"username": "hidden_actor"}, "errors": []}

    me_res = schema.execute_sync(_ME_Q, context_value=request)
    assert me_res.errors is None, me_res.errors
    assert me_res.data["me"] == {"username": "hidden_actor"}
