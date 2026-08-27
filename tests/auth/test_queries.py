"""Current-user query tests for alias binding, visibility, permission gates, and sync/async resolution.

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

from unittest import mock

import pytest
import strawberry
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.utils.functional import SimpleLazyObject
from strawberry import relay

from django_strawberry_framework import DjangoSchema, DjangoType, finalize_django_types
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
from tests.auth._helpers import _session_request

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


def _me_schema(**current_user_kwargs) -> strawberry.Schema:
    """Declare UserT + a me-only Query; return the finalized schema."""
    _declare_user_type()

    @strawberry.type
    class Query:
        me = current_user(**current_user_kwargs)

    finalize_django_types()
    return DjangoSchema(query=Query)


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
def test_sync_me_dispatch_never_enters_the_async_boundary(_sync_boundary_spy):
    """``execute_sync`` ``me`` runs the native sync body with no event-loop bridge."""
    schema = _me_schema()
    user = User.objects.create_user(username="me_sync", password="pw-9x-strong")
    res = schema.execute_sync(_ME_Q, context_value=_session_request(user))
    assert res.errors is None, res.errors
    assert res.data["me"] == {"username": "me_sync"}
    assert _sync_boundary_spy == []


@pytest.mark.django_db(transaction=True)
async def test_async_me_dispatch_awaits_the_native_async_body_exactly_once(_sync_boundary_spy):
    """``await schema.execute`` ``me`` awaits the native async body exactly once."""
    schema = _me_schema()
    user = await User.objects.acreate_user(username="me_async", password="pw-9x-strong")
    res = await schema.execute(_ME_Q, context_value=_session_request(user))
    assert res.errors is None, res.errors
    assert res.data["me"] == {"username": "me_async"}
    assert len(_sync_boundary_spy) == 1


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
def test_me_accepts_a_regular_mapping_context_with_a_django_request():
    """A direct ``Schema.execute`` mapping context carries its Django request to ``me``."""
    schema = _me_schema()
    user = User.objects.create_user(username="mapping_me", password="pw-9x-strong")

    result = schema.execute_sync(_ME_Q, context_value={"request": _session_request(user)})

    assert result.errors is None, result.errors
    assert result.data["me"] == {"username": "mapping_me"}


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

    # A SimpleLazyObject returning None (lazy unauthenticated user resolving to None).
    lazy_none = RequestFactory().post("/graphql/")
    lazy_none.user = SimpleLazyObject(lambda: None)
    lazy_none_res = schema.execute_sync(_ME_Q, context_value=lazy_none)
    assert lazy_none_res.errors is None, lazy_none_res.errors
    assert lazy_none_res.data["me"] is None

    # A custom actor object without is_authenticated attribute.
    custom_actor = RequestFactory().post("/graphql/")
    custom_actor.user = object()
    custom_res = schema.execute_sync(_ME_Q, context_value=custom_actor)
    assert custom_res.errors is None, custom_res.errors
    assert custom_res.data["me"] is None


@pytest.mark.django_db
def test_hostile_user_descriptor_raising_collapses_to_anonymous_null():
    """Hostile ``request.user`` / ``is_authenticated`` raising TypeError/ValueError collapses to ``null``.

    Exception containment (hunt 0.0.14): a hostile descriptor or a hostile
    ``is_authenticated`` that raises ``TypeError`` / ``ValueError`` /
    ``AttributeError`` / ``KeyError`` / ``IndexError`` must not escape as an
    unhandled top-level error. Those shapes collapse to anonymous (``None``) -
    a fail-closed nullable return - while any other exception (e.g. a
    ``DatabaseError`` from a ``SimpleLazyObject`` that hits the DB) is left to
    propagate.
    """
    from django.http import HttpRequest

    class HostileRequest(HttpRequest):
        @property
        def user(self):
            raise TypeError("hostile user getter")

    schema = _me_schema()
    hostile_req = HostileRequest()
    hostile_req.method = "POST"
    res = schema.execute_sync(_ME_Q, context_value=hostile_req)
    assert res.errors is None, res.errors
    assert res.data["me"] is None

    class HostileIsAuth:
        @property
        def is_authenticated(self):
            raise ValueError("hostile is_authenticated")

    req = RequestFactory().post("/graphql/")
    req.user = HostileIsAuth()
    res2 = schema.execute_sync(_ME_Q, context_value=req)
    assert res2.errors is None, res2.errors
    assert res2.data["me"] is None


def test_current_user_hostile_directives_raise_configuration_error():
    """A hostile ``directives`` iterable or a bare string must raise ``ConfigurationError``."""

    class HostileIter:
        def __iter__(self):
            raise ValueError("hostile directives")

    with pytest.raises(ConfigurationError):
        current_user(directives=HostileIter())

    with pytest.raises(ConfigurationError):
        current_user(directives="oops")


def _legacy_callable_user(outcome):
    """Patch the concrete user model's ``is_authenticated`` into a pre-1.10 CALLABLE.

    ``mock.patch.object`` deletes the shadowing attribute on exit because the
    real one is inherited from ``AbstractBaseUser``, so the model class is left
    exactly as found. Patching the real model (rather than substituting a duck
    object) is what keeps the authenticated arm serializable: the ``me`` field's
    return type is the concrete ``UserT``, and GraphQL rejects anything else.
    """

    def _is_authenticated(self):
        return outcome()

    return mock.patch.object(User, "is_authenticated", _is_authenticated)


@pytest.mark.django_db
def test_legacy_callable_is_authenticated_is_called_and_authenticates():
    """A legacy ``is_authenticated()`` returning true resolves to the actor, not ``null``."""
    User.objects.create_user(username="legacy", password="pw")
    schema = _me_schema()
    req = RequestFactory().post("/graphql/")
    req.user = User.objects.get(username="legacy")

    with _legacy_callable_user(lambda: True):
        res = schema.execute_sync(_ME_Q, context_value=req)

    assert res.errors is None, res.errors
    assert res.data["me"]["username"] == "legacy"


@pytest.mark.django_db
def test_legacy_callable_is_authenticated_returning_false_is_anonymous():
    """A legacy ``is_authenticated()`` returning false is the anonymous ``null``."""
    User.objects.create_user(username="legacy-off", password="pw")
    schema = _me_schema()
    req = RequestFactory().post("/graphql/")
    req.user = User.objects.get(username="legacy-off")

    with _legacy_callable_user(lambda: False):
        res = schema.execute_sync(_ME_Q, context_value=req)

    assert res.errors is None, res.errors
    assert res.data["me"] is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "raised",
    [
        TypeError,
        ValueError,
        AttributeError,
        KeyError,
        IndexError,
    ],
)
def test_legacy_callable_is_authenticated_raising_collapses_to_anonymous_null(raised):
    """A legacy ``is_authenticated()`` raising any of the five shapes collapses to ``null``.

    The CALL is a third hostile surface alongside the ``request.user`` and
    ``user.is_authenticated`` reads: a pre-1.10 callable that raises must not
    escape as an unhandled top-level error carrying the hostile message.
    """
    User.objects.create_user(username="legacy-hostile", password="pw")
    schema = _me_schema()
    req = RequestFactory().post("/graphql/")
    req.user = User.objects.get(username="legacy-hostile")

    def _raise():
        raise raised("hostile is_authenticated()")

    with _legacy_callable_user(_raise):
        res = schema.execute_sync(_ME_Q, context_value=req)

    assert res.errors is None, res.errors
    assert res.data["me"] is None


@pytest.mark.django_db
def test_awaitable_is_authenticated_is_closed_and_read_as_anonymous():
    """A NON-callable awaitable ``is_authenticated`` is closed and read as anonymous.

    A pending coroutine is neither true nor false; leaving it unawaited would
    also leak a "never awaited" warning out of the resolver. The helper closes
    it and classifies the request as anonymous.
    """

    async def _pending():  # pragma: no cover - closed, never awaited
        return True

    coro = _pending()

    class _AwaitableIsAuth:
        is_authenticated = coro

    schema = _me_schema()
    req = RequestFactory().post("/graphql/")
    req.user = _AwaitableIsAuth()
    res = schema.execute_sync(_ME_Q, context_value=req)
    assert res.errors is None, res.errors
    assert res.data["me"] is None
    # Closed by the helper: awaiting a closed coroutine is a RuntimeError.
    with pytest.raises(RuntimeError):
        coro.send(None)


@pytest.mark.django_db
def test_legacy_callable_returning_an_awaitable_is_closed_and_read_as_anonymous():
    """A legacy ``is_authenticated()`` returning a coroutine is closed, not awaited."""
    captured = []

    class _AsyncCallableIsAuth:
        def is_authenticated(self):
            async def _pending():  # pragma: no cover - closed, never awaited
                return True

            coro = _pending()
            captured.append(coro)
            return coro

    schema = _me_schema()
    req = RequestFactory().post("/graphql/")
    req.user = _AsyncCallableIsAuth()
    res = schema.execute_sync(_ME_Q, context_value=req)
    assert res.errors is None, res.errors
    assert res.data["me"] is None
    assert len(captured) == 1
    with pytest.raises(RuntimeError):
        captured[0].send(None)


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

    The spec-040 Decision 10 async-gate fix: computing the gate argument forces the lazy
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
    schema = DjangoSchema(query=Query, mutation=Mutation)

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
