"""Auth mutation tests for declaration and bind lifecycles, operations, registration, and permissions.

Only the residue a realistic fakeshop ``/graphql/`` request cannot drive lives
here (the AGENTS.md placement rule; the live consumer surface is
``examples/fakeshop/test_query/test_auth_api.py``): the declaration-ledger
lifecycle (survive-the-pre-bind-reset / ``registry.clear()`` drain /
reload-idempotence / the conflicting-``permission_classes`` raise), the
surface-keyed bind validation arms, the post-finalize factory reject, the async
resolver paths, the sessionless edge, the async-permission ``SyncMisuseError``,
the register rider internals (``derive_register_fields``, the exclusion seam's
provided-marker contract, plaintext-never-persisted on BOTH resolver paths,
hash-before-``full_clean`` ordering), and the permission-gate variants - the
gated fixed-payload fields cannot coexist with the aggregate fakeshop default
surface under the one-declaration-per-process rule, so their exact denial
strings are pinned here on isolated throwaway schemas.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import itertools
import json
import logging
import threading

import pytest
import strawberry
from apps.products.services import TEST_USER_PASSWORD, create_users
from channels.db import database_sync_to_async
from channels.testing import HttpCommunicator, WebsocketCommunicator
from django.conf import settings
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    SESSION_KEY,
    get_user_model,
)
from django.contrib.auth import (
    signals as auth_signals,
)
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.backends.db import SessionStore as DBSessionStore
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied
from django.db import models as djmodels
from django.test import RequestFactory, override_settings
from strawberry import relay

from django_strawberry_framework import DjangoSchema, DjangoType, finalize_django_types
from django_strawberry_framework.auth import (
    current_user,
    login_mutation,
    logout_mutation,
    register_mutation,
)
from django_strawberry_framework.auth import mutations as auth_mutations
from django_strawberry_framework.auth.mutations import (
    _auth_declarations,
    _declared_auth_surface,
    _sync_bridged_async_body,
    bind_auth_mutations,
    derive_register_fields,
    iter_auth_mutations,
)
from django_strawberry_framework.auth.sessions import _SCOPE_LOCK_KEY
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations import inputs as mutation_inputs
from django_strawberry_framework.mutations.inputs import _materialized_names
from django_strawberry_framework.mutations.resolvers import _model_decode_step
from django_strawberry_framework.mutations.sets import _mutation_registry
from django_strawberry_framework.registry import (
    iter_subsystem_clears,
    registry,
)
from django_strawberry_framework.utils.permissions import ChannelsRequestAdapter
from django_strawberry_framework.utils.querysets import SyncMisuseError
from tests.auth._helpers import _drain_until, _session_request

User = get_user_model()

# The async seeding twin: ``create_users`` wrapped once for the async tests, rather
# than re-wrapping ``database_sync_to_async(create_users)`` at every await site.
_acreate_users = database_sync_to_async(create_users)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry (co-clearing the auth declaration ledger) per test."""
    registry.clear()
    yield
    registry.clear()


_app_label_counter = itertools.count(1)


def _unique_app_label() -> str:
    """Return a unique ``app_label`` per call to avoid Django's re-register warning."""
    return f"test_auth_mutations__{next(_app_label_counter)}"


class _AllowAll:
    """A permission class that authorizes every request (a non-default gate fixture)."""

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        return True


class _DenyAll:
    """A permission class that denies every request (drives the exact denial strings)."""

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        return False


def _declare_user_type(fields=("id", "username", "email")):
    """Register a fresh Relay-backed primary ``DjangoType`` over the user model.

    ``fields`` seams the exposed column set: the default identity trio, or a
    ``last_login``-exposing variant for the post-login-signal invariant tests.
    """
    return type(
        "UserT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": User, "fields": fields, "primary": True},
            ),
        },
    )


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _finalize_schema(mutation_type: type, *, query_type: type = _Query) -> strawberry.Schema:
    finalize_django_types()
    return DjangoSchema(query=query_type, mutation=mutation_type)


def _login_logout_schema(*, declare=_declare_user_type, query_type=_Query, **login_kwargs):
    """Declare the user type + a login/logout Mutation; return the finalized schema.

    ``declare`` is the per-call user-type declaration callable (default the plain
    identity-trio type; a ``last_login``-exposing variant swaps it in). ``query_type``
    seams a richer Query in - e.g. one carrying ``me`` for the router tests - and must
    be built by the caller so its auth field factories run inside the per-test cleared
    registry. ``login_kwargs`` flow to ``login_mutation``.
    """
    declare()

    @strawberry.type
    class Mutation:
        login = login_mutation(**login_kwargs)
        logout = logout_mutation()

    return _finalize_schema(Mutation, query_type=query_type)


def _channels_adapter(scope_type="http", *, store=None, user=None):
    """Build a ``ChannelsRequestAdapter`` over a fabricated ASGI scope.

    The ONE factory the Channels-transport tests share for the repeated
    ``ChannelsRequestAdapter(RequestFactory().post("/graphql/"), {...})`` shape.
    ``scope_type`` is the ASGI ``type`` (``"http"`` / ``"websocket"``); ``store``
    defaults to a fresh ``DBSessionStore()`` and ``user`` to ``AnonymousUser()``
    (fresh per call - never a shared mutable default), while tests that name their
    own store/actor pass them explicitly.
    """
    return ChannelsRequestAdapter(
        RequestFactory().post("/graphql/"),
        {
            "type": scope_type,
            "session": store if store is not None else DBSessionStore(),
            "user": user if user is not None else AnonymousUser(),
        },
    )


_LOGIN_Q = (
    'mutation($p: String!){ login(username: "probe", password: $p){ '
    "node{ username } errors{ field messages } } }"
)
_LOGOUT_Q = "mutation{ logout{ ok errors{ field } } }"


# ---------------------------------------------------------------------------
# Declaration-ledger mechanics
# ---------------------------------------------------------------------------


def test_same_args_factory_calls_dedupe_to_one_cached_holder():
    """A repeat same-``permission_classes`` call returns the identity-cached holder."""
    login_mutation()
    holder = _declared_auth_surface("login")
    login_mutation()
    assert _declared_auth_surface("login") is holder
    assert len(_auth_declarations) == 1


def test_presentation_kwargs_never_enter_the_conflict_key():
    """``description`` / ``deprecation_reason`` / ``directives`` deltas never raise."""
    login_mutation(description="A")
    holder = _declared_auth_surface("login")
    login_mutation(description="B", deprecation_reason="old")
    assert _declared_auth_surface("login") is holder
    assert len(_auth_declarations) == 1


def test_conflicting_permission_classes_second_call_raises():
    """A different-``permission_classes`` repeat is the loud one-declaration raise."""
    login_mutation()
    with pytest.raises(ConfigurationError, match=r"auth login_mutation\(\) is already declared"):
        login_mutation(permission_classes=[_AllowAll])


def test_declarations_survive_the_pre_bind_reset():
    """The pre-bind emit-ledger reset never touches the auth DECLARATION ledger."""
    login_mutation()
    logout_mutation()
    assert len(_auth_declarations) == 2
    for clear in iter_subsystem_clears(before_bind=True):
        clear()
    assert len(_auth_declarations) == 2


def test_registry_clear_drains_ledger_and_resets_conflict_state():
    """``registry.clear()`` drains the ledger; a post-clear re-gate mints a fresh holder."""
    login_mutation()
    stale_holder = _declared_auth_surface("login")
    registry.clear()
    assert iter_auth_mutations() == ()
    # The prior declaration (and so the conflict state) did not survive the clear:
    # a different-``permission_classes`` re-declaration succeeds with a NEW holder.
    login_mutation(permission_classes=[_AllowAll])
    fresh_holder = _declared_auth_surface("login")
    assert fresh_holder is not stale_holder
    assert fresh_holder._mutation_meta.permission_classes == [_AllowAll]


def test_registry_clear_does_not_import_the_auth_subsystem():
    """``registry.clear()`` in an auth-free process never imports ``auth.mutations``.

    The structural opt-in (spec-040 Decision 3) covers BOTH consumer-reachable
    paths: the finalizer's bind is guarded on ``sys.modules``, and a clear
    callback only exists on the registry once its owner module has been
    imported and self-registered - so clearing can never import an unloaded
    subsystem as a side effect. Subprocess-based so the assertion is
    deterministic regardless of what this worker already imported.
    """
    import subprocess
    import sys
    from pathlib import Path

    fakeshop = Path(__file__).resolve().parents[2] / "examples" / "fakeshop"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import django; "
                "import os; "
                f"import sys; sys.path.insert(0, {str(fakeshop)!r}); "
                "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); "
                "django.setup(); "
                "import django_strawberry_framework.registry as r; "
                "r.registry.clear(); "
                "assert 'django_strawberry_framework.auth.mutations' not in sys.modules"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"subprocess failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


def test_factory_after_finalize_raises_the_standing_configuration_error():
    """The declare-after-finalize rule covers the fixed factories and the rider synthesis."""
    _login_logout_schema()
    with pytest.raises(ConfigurationError, match="after finalization"):
        login_mutation()
    with pytest.raises(ConfigurationError, match="after finalization"):
        register_mutation()


def test_register_factory_recache_and_reregister_on_every_call():
    """Same-args ``register_mutation()`` reuses the one rider and re-records BOTH ledgers."""
    register_mutation()
    rider = _declared_auth_surface("register")
    assert rider.__name__ == "Register"
    register_mutation()
    assert _declared_auth_surface("register") is rider
    assert _mutation_registry.count(rider) == 1
    assert _auth_declarations.count(rider) == 1
    with pytest.raises(
        ConfigurationError,
        match=r"auth register_mutation\(\) is already declared",
    ):
        register_mutation(permission_classes=[_AllowAll])


# ---------------------------------------------------------------------------
# Surface-keyed bind validation (Decision 8 / Decision 9)
# ---------------------------------------------------------------------------

_LOGIN_ARM_ERROR = (
    r"auth login_mutation\(\) declared with no registered DjangoType for the user model User"
)
_REGISTER_ARM_ERROR = (
    r"auth register_mutation\(\) declared with no registered DjangoType for the user model User"
)


def test_login_only_schema_without_user_type_raises_the_login_arm_error():
    login_mutation()
    with pytest.raises(ConfigurationError, match=_LOGIN_ARM_ERROR):
        finalize_django_types()


def test_register_only_schema_without_user_type_raises_the_register_arm_error():
    """The auth-specific register arm pre-empts ``_resolve_primary_type``'s generic message."""
    register_mutation()
    with pytest.raises(ConfigurationError, match=_REGISTER_ARM_ERROR) as excinfo:
        finalize_django_types()
    # Never the generic mutation-bind wording (which names the internal ``Register``
    # class and the raw model with no ``get_user_model()`` recourse).
    assert "has no registered DjangoType; the mutation has no type to return" not in str(
        excinfo.value,
    )


def test_ambiguous_user_primary_raises_the_set_meta_primary_message():
    """Two user types with no declared primary split onto the ambiguity message."""
    registry.register(User, type("UserA", (), {}))
    registry.register(User, type("UserB", (), {}))
    login_mutation()
    with pytest.raises(ConfigurationError, match="multiple registered DjangoTypes"):
        bind_auth_mutations()


def test_logout_only_schema_binds_with_no_user_type_and_no_orphan_payloads():
    """The structural logout exemption: no primary resolved, only ``LogoutPayload`` emitted."""

    @strawberry.type
    class Mutation:
        logout = logout_mutation()

    schema = _finalize_schema(Mutation)
    assert "LogoutPayload" in _materialized_names
    assert "LoginPayload" not in _materialized_names
    assert "logout" in str(schema)


@pytest.mark.django_db
def test_logout_without_auth_middleware_is_anonymous_and_flushes_the_session():
    """A session-only request has no actor but still receives Django's teardown."""

    @strawberry.type
    class Mutation:
        logout = logout_mutation()

    schema = _finalize_schema(Mutation)
    request = RequestFactory().post("/graphql/")
    SessionMiddleware(lambda _request: None).process_request(request)
    request.session["logout_residue"] = "must be flushed"
    request.session.save()

    result = schema.execute_sync(_LOGOUT_Q, context_value=request)

    assert result.errors is None, result.errors
    assert result.data["logout"] == {"ok": False, "errors": []}
    assert "logout_residue" not in request.session


def test_login_only_bind_emits_no_orphan_logout_payload():
    """The surface-keyed bind materializes only the DECLARED surfaces' payloads."""
    _declare_user_type()

    @strawberry.type
    class Mutation:
        login = login_mutation()

    _finalize_schema(Mutation)
    assert "LoginPayload" in _materialized_names
    assert "LogoutPayload" not in _materialized_names


def test_register_only_surface_keyed_bind_emits_no_login_logout_payloads():
    """A register-only schema materializes ``RegisterInput`` / ``RegisterPayload`` only."""
    _declare_user_type()

    @strawberry.type
    class Mutation:
        register = register_mutation()

    _finalize_schema(Mutation)
    assert "RegisterInput" in _materialized_names
    assert "RegisterPayload" in _materialized_names
    assert "LoginPayload" not in _materialized_names
    assert "LogoutPayload" not in _materialized_names


def test_reload_idempotence_cycle_rebuilds_the_full_auth_surface():
    """finalize -> ``registry.clear()`` -> re-declare -> finalize reconstructs everything."""
    first = _login_logout_schema()
    assert "login" in str(first)

    registry.clear()
    _declare_user_type()

    @strawberry.type
    class Mutation:
        login = login_mutation()
        logout = logout_mutation()
        register = register_mutation()

    second = _finalize_schema(Mutation)
    sdl = str(second)
    assert "login" in sdl
    assert "register(data: RegisterInput!): RegisterPayload!" in sdl


def test_register_arm_error_survives_a_reload_cycle():
    """After clear + re-declare, the SECOND finalize still fires the auth-specific arm.

    Pins the every-call auth-ledger re-record (spec-040 Revision 4 P2): were the
    auth-ledger record written once behind the cache guard, the drained ledger
    would leave ``bind_auth_mutations()`` blind to ``register`` on the second
    finalize and the generic ``_resolve_primary_type`` message would regress in.
    """
    register_mutation()
    with pytest.raises(ConfigurationError, match=_REGISTER_ARM_ERROR):
        finalize_django_types()

    registry.clear()
    register_mutation()
    with pytest.raises(ConfigurationError, match=_REGISTER_ARM_ERROR):
        finalize_django_types()


# ---------------------------------------------------------------------------
# Native sync / async dispatch seam (auth session-lifecycle hardening Commit 2)
# ---------------------------------------------------------------------------


def test_bridged_async_body_is_a_real_coroutine_function():
    """The async resolver body is a genuine ``async def`` (not a sync body in disguise)."""
    body = _sync_bridged_async_body(lambda info, **kwargs: None)
    assert inspect.iscoroutinefunction(body)


def test_auth_field_dispatch_splits_sync_and_async_resolver_bodies():
    """``_make_auth_field`` picks the sync body vs the async body by ``in_async_context``."""
    sync_calls = []
    async_calls = []

    def _sync_body(info, **kwargs):
        sync_calls.append(kwargs)
        return "sync"

    async def _async_body(info, **kwargs):
        async_calls.append(kwargs)
        return "async"

    field = auth_mutations._make_auth_field(
        sync_body=_sync_body,
        async_body=_async_body,
        arguments=[],
        return_annotation=str,
        description=None,
        deprecation_reason=None,
        directives=(),
    )
    resolver = field.base_resolver.wrapped_func

    # Sync execution stays synchronous: the plain sync body runs and returns a value.
    assert resolver(None, info=None) == "sync"
    assert len(sync_calls) == 1
    assert async_calls == []


@pytest.mark.django_db
def test_sync_login_dispatch_never_enters_the_async_boundary(_sync_boundary_spy):
    """``execute_sync`` login runs the native sync body with no event-loop bridge."""
    schema = _login_logout_schema()
    get_user_model().objects.create_user(username="probe", password="pw-9x-strong")

    res = schema.execute_sync(
        _LOGIN_Q,
        variable_values={"p": "pw-9x-strong"},
        context_value=_session_request(),
    )
    assert res.errors is None, res.errors
    assert res.data["login"] == {"node": {"username": "probe"}, "errors": []}
    # Sync dispatch never touched the async body's one-sync-boundary bridge.
    assert _sync_boundary_spy == []


@pytest.mark.django_db(transaction=True)
async def test_async_login_dispatch_awaits_the_native_async_body_exactly_once(_sync_boundary_spy):
    """``await schema.execute`` login awaits the native async body exactly once."""
    schema = _login_logout_schema()
    await get_user_model().objects.acreate_user(username="probe", password="pw-9x-strong")

    request = _session_request()
    res = await schema.execute(
        _LOGIN_Q,
        variable_values={"p": "pw-9x-strong"},
        context_value=request,
    )
    assert res.errors is None, res.errors
    assert res.data["login"] == {"node": {"username": "probe"}, "errors": []}
    assert request.user.is_authenticated
    assert len(_sync_boundary_spy) == 1


@pytest.mark.django_db
def test_sync_logout_dispatch_never_enters_the_async_boundary(_sync_boundary_spy):
    """``execute_sync`` logout runs the native sync body with no event-loop bridge."""
    schema = _login_logout_schema()
    res = schema.execute_sync(_LOGOUT_Q, context_value=_session_request())
    assert res.errors is None, res.errors
    assert res.data["logout"] == {"ok": False, "errors": []}
    assert _sync_boundary_spy == []


@pytest.mark.django_db(transaction=True)
async def test_async_logout_dispatch_awaits_the_native_async_body_exactly_once(_sync_boundary_spy):
    """``await schema.execute`` logout awaits the native async body exactly once."""
    schema = _login_logout_schema()
    res = await schema.execute(_LOGOUT_Q, context_value=_session_request())
    assert res.errors is None, res.errors
    assert res.data["logout"] == {"ok": False, "errors": []}
    assert len(_sync_boundary_spy) == 1


def test_auth_field_sdl_signatures_are_unchanged_by_the_dispatch_split():
    """The public SDL for the auth fields/payloads is byte-stable across the seam."""
    schema = _login_logout_schema()
    sdl = str(schema)
    assert "login(username: String!, password: String!): LoginPayload!" in sdl
    assert "logout: LogoutPayload!" in sdl
    assert "type LoginPayload {" in sdl
    assert "type LogoutPayload {" in sdl


# ---------------------------------------------------------------------------
# Session resolvers: async paths, sessionless edge, async-permission misuse
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_async_login_and_logout_run_in_one_sync_boundary():
    """The async twins work end to end (gate + session work inside one worker)."""
    schema = _login_logout_schema()
    user_model = get_user_model()
    await user_model.objects.acreate_user(username="probe", password="pw-9x-strong")

    request = _session_request()
    res = await schema.execute(
        _LOGIN_Q,
        variable_values={"p": "pw-9x-strong"},
        context_value=request,
    )
    assert res.errors is None, res.errors
    assert res.data["login"] == {"node": {"username": "probe"}, "errors": []}
    assert request.user.is_authenticated

    res = await schema.execute(_LOGOUT_Q, context_value=request)
    assert res.errors is None, res.errors
    assert res.data["logout"] == {"ok": True, "errors": []}
    assert not request.user.is_authenticated


@pytest.mark.django_db(transaction=True)
async def test_async_register_never_persists_the_plaintext():
    """The async register override (a separate seam) also stores only the hash."""
    _declare_user_type()

    @strawberry.type
    class Mutation:
        register = register_mutation()

    schema = _finalize_schema(Mutation)
    res = await schema.execute(
        'mutation{ register(data: {username: "async_reg", password: "pw-9x-strong"}){ '
        "node{ username } errors{ field } } }",
        context_value=_session_request(),
    )
    assert res.errors is None, res.errors
    assert res.data["register"]["node"] == {"username": "async_reg"}
    stored = await get_user_model().objects.aget(username="async_reg")
    assert "pw-9x-strong" not in stored.password
    assert stored.check_password("pw-9x-strong")


@pytest.mark.django_db
def test_sessionless_request_surfaces_djangos_own_error():
    """No session stack -> Django's error propagates (no bespoke probe, no swallow)."""
    schema = _login_logout_schema()
    user_model = get_user_model()
    user_model.objects.create_user(username="probe", password="pw-9x-strong")
    request = RequestFactory().post("/graphql/")  # deliberately no SessionMiddleware
    request.user = AnonymousUser()
    res = schema.execute_sync(
        _LOGIN_Q,
        variable_values={"p": "pw-9x-strong"},
        context_value=request,
    )
    assert res.errors is not None
    assert "session" in res.errors[0].message.lower()


@pytest.mark.django_db
def test_async_has_permission_raises_sync_misuse_never_a_silent_allow():
    """An ``async def has_permission`` is a ``SyncMisuseError``, not an authorization bypass."""

    class AsyncGate:
        async def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return False

    schema = _login_logout_schema(permission_classes=[AsyncGate])
    res = schema.execute_sync(
        _LOGIN_Q,
        variable_values={"p": "x"},
        context_value=_session_request(),
    )
    assert res.errors is not None
    assert "AsyncGate.has_permission returned a coroutine" in res.errors[0].message


@pytest.mark.django_db
async def test_async_permission_hook_rejected_inside_the_sync_worker_too():
    """The ``SyncMisuseError`` discipline holds inside the one ``sync_to_async`` boundary."""

    class AsyncGate:
        async def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return False

    schema = _login_logout_schema(permission_classes=[AsyncGate])
    res = await schema.execute(
        _LOGIN_Q,
        variable_values={"p": "x"},
        context_value=_session_request(),
    )
    assert res.errors is not None
    assert "AsyncGate.has_permission returned a coroutine" in res.errors[0].message
    assert isinstance(res.errors[0].original_error, SyncMisuseError)


# ---------------------------------------------------------------------------
# Permission-gate variants (unreachable live under one-declaration-per-process)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_gated_login_denies_with_the_exact_pinned_string_before_authenticate():
    schema = _login_logout_schema(permission_classes=[_DenyAll])
    res = schema.execute_sync(
        _LOGIN_Q,
        variable_values={"p": "x"},
        context_value=_session_request(),
    )
    assert res.errors is not None
    assert res.errors[0].message == "Not authorized to login UserT."


@pytest.mark.django_db
def test_gated_logout_denies_with_the_session_holder_string():
    """The model-less denial target IS the pinned holder ``__name__`` (``Session``)."""
    _declare_user_type()

    @strawberry.type
    class Mutation:
        login = login_mutation()
        logout = logout_mutation(permission_classes=[_DenyAll])

    schema = _finalize_schema(Mutation)
    res = schema.execute_sync(_LOGOUT_Q, context_value=_session_request())
    assert res.errors is not None
    assert res.errors[0].message == "Not authorized to logout Session."


@pytest.mark.django_db
def test_gated_register_denies_with_the_standard_create_string():
    """``register`` is a real ``DjangoMutation``: the standard create denial applies."""
    _declare_user_type()

    @strawberry.type
    class Mutation:
        register = register_mutation(permission_classes=[_DenyAll])

    schema = _finalize_schema(Mutation)
    res = schema.execute_sync(
        'mutation{ register(data: {username: "nope", password: "pw-9x-strong"}){ '
        "errors{ field } } }",
        context_value=_session_request(),
    )
    assert res.errors is not None
    assert res.errors[0].message == "Not authorized to create UserT."
    assert not get_user_model().objects.filter(username="nope").exists()


@pytest.mark.django_db
def test_login_gate_sees_the_attempted_username_and_never_the_password():
    """The pinned gate payload: ``data = {"username": ...}``, ``instance=None``."""
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

    schema = _login_logout_schema(permission_classes=[RecordingGate])
    schema.execute_sync(
        _LOGIN_Q,
        variable_values={"p": "sekrit"},
        context_value=_session_request(),
    )
    assert seen["operation"] == "login"
    assert seen["data"] == {"username": "probe"}
    assert "sekrit" not in str(seen["data"])
    assert seen["instance"] is None


@pytest.mark.django_db
def test_gate_introspecting_the_mutation_object_raises_on_the_model_less_fields():
    """A gate reading ``mutation.Meta.model`` raises at request time (documented, not guarded).

    The ``mutation`` positional on ``login`` / ``logout`` / ``current_user`` is
    the internal permission holder - no ``Meta.model``, no ``_resolve_model`` -
    so gates must key on ``info`` / ``operation`` / ``data`` (spec-040 Decision
    5); one keyed that way authorizes fine, one that introspects the object
    raises the request-time error the ``DenyAll`` precedent documents.
    """
    seen_holders = []

    class InfoKeyedGate:
        def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            seen_holders.append(mutation)
            return operation == "logout"

    class ModelIntrospectingGate:
        def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return mutation.Meta.model is not None

    _declare_user_type()

    @strawberry.type
    class Mutation:
        login = login_mutation(permission_classes=[ModelIntrospectingGate])
        logout = logout_mutation(permission_classes=[InfoKeyedGate])

    schema = _finalize_schema(Mutation)
    ok = schema.execute_sync(_LOGOUT_Q, context_value=_session_request())
    assert ok.errors is None, ok.errors
    assert seen_holders[0].__name__ == "Session"  # the holder, not a DjangoMutation

    broken = schema.execute_sync(
        _LOGIN_Q,
        variable_values={"p": "x"},
        context_value=_session_request(),
    )
    assert broken.errors is not None  # the request-time raise, never a silent allow


# ---------------------------------------------------------------------------
# Register rider internals
# ---------------------------------------------------------------------------


def test_derive_register_fields_default_user_model():
    assert derive_register_fields(User) == ("username", "email", "password")


def test_derive_register_fields_custom_username_and_required_fields():
    """A custom-``USERNAME_FIELD`` model derives + dedupes in declaration order."""

    class CustomLoginUser(djmodels.Model):
        email = djmodels.EmailField(unique=True)
        nickname = djmodels.CharField(max_length=50)
        password = djmodels.CharField(max_length=128)

        USERNAME_FIELD = "email"
        # ``email`` repeats USERNAME_FIELD and ``password`` repeats the fixed
        # tail - both appear exactly once in the derived tuple.
        REQUIRED_FIELDS = ("nickname", "email", "password")

        class Meta:
            app_label = _unique_app_label()

    assert derive_register_fields(CustomLoginUser) == ("email", "nickname", "password")


def test_derive_register_fields_rejects_privilege_fields():
    """A custom model cannot turn ``is_staff`` into public registration input."""

    class PrivilegeRequiredUser(djmodels.Model):
        username = djmodels.CharField(max_length=150)
        password = djmodels.CharField(max_length=128)
        is_staff = djmodels.BooleanField(default=False)

        USERNAME_FIELD = "username"
        REQUIRED_FIELDS = ("is_staff",)

        class Meta:
            app_label = _unique_app_label()

    with pytest.raises(
        ConfigurationError,
        match=(
            r"register_mutation\(\) cannot auto-expose protected user field\(s\) "
            r"\['is_staff'\].*PrivilegeRequiredUser"
        ),
    ):
        derive_register_fields(PrivilegeRequiredUser)


def test_derive_register_fields_rejects_unknown_names_via_editable_input_fields():
    """Unknown / non-editable names delegate to the standard narrowing reject."""

    class BrokenRequiredUser(djmodels.Model):
        handle = djmodels.CharField(max_length=50)
        password = djmodels.CharField(max_length=128)

        USERNAME_FIELD = "handle"
        REQUIRED_FIELDS = ("no_such_column",)

        class Meta:
            app_label = _unique_app_label()

    with pytest.raises(ConfigurationError, match=r"\['no_such_column'\]"):
        derive_register_fields(BrokenRequiredUser)


def test_exclusion_seam_captures_password_and_preserves_the_provided_marker():
    """The spec-040 D6 seam: value captured, marker preserved, attr never constructed."""

    @strawberry.input
    class ProbeRegisterInput:
        username: str
        password: str

    data = ProbeRegisterInput(username="seam_probe", password="raw-secret")
    decoded = _model_decode_step(
        User,
        data,
        info=None,
        instance=None,
        excluded_input_fields=frozenset({"password"}),
    )
    target, m2m_assignments, exclude, excluded_values = decoded
    # The raw value was captured out of the constructed attrs...
    assert excluded_values == {"password": "raw-secret"}
    # ...never reaching the model instance (a fresh User carries the empty default)...
    assert target.password == ""
    assert target.username == "seam_probe"
    assert m2m_assignments == []
    # ...while the AR-H2 exclude calculation still counts ``password`` as PROVIDED
    # (an unprovided column like ``email`` is excluded; ``password`` is not).
    assert "password" not in exclude
    assert "email" in exclude


def test_model_decode_step_without_exclusion_keeps_the_historical_three_tuple():
    """The default no-exclusion call is byte-compatible with the model flavor."""

    @strawberry.input
    class ProbeInput:
        username: str

    decoded = _model_decode_step(User, ProbeInput(username="plain"), info=None, instance=None)
    assert len(decoded) == 3


@pytest.mark.django_db
def test_sync_register_never_persists_the_plaintext_and_hashes_before_full_clean():
    """The sync path stores only the hash; hashing precedes ``full_clean``.

    The ordering proof: a >128-char password would fail the ``password`` column's
    ``max_length`` validation if the RAW value were assigned before
    ``full_clean()``; because ``set_password`` runs first, the column validates
    against the (fixed-width) hash and the register succeeds.
    """
    _declare_user_type()

    @strawberry.type
    class Mutation:
        register = register_mutation()

    schema = _finalize_schema(Mutation)
    long_password = "x9-" + "long-strong-" * 12  # 147 chars > the 128-char column
    assert len(long_password) > 128
    res = schema.execute_sync(
        'mutation($p: String!){ register(data: {username: "sync_reg", password: $p}){ '
        "node{ username } errors{ field messages } } }",
        variable_values={"p": long_password},
        context_value=_session_request(),
    )
    assert res.errors is None, res.errors
    assert res.data["register"] == {"node": {"username": "sync_reg"}, "errors": []}
    stored = get_user_model().objects.get(username="sync_reg")
    assert long_password not in stored.password
    assert stored.check_password(long_password)


def test_register_input_name_is_pinned_and_payload_derives_from_the_rider_name():
    """``RegisterInput`` via the name seams; ``RegisterPayload`` from ``__name__`` alone."""
    _declare_user_type()

    @strawberry.type
    class Mutation:
        register = register_mutation()

    schema = _finalize_schema(Mutation)
    sdl = str(schema)
    assert "input RegisterInput" in sdl
    assert "type RegisterPayload" in sdl
    # The deterministic shape-derived name never leaks into the schema.
    assert "UserEmailPasswordUsernameInput" not in sdl
    assert mutation_inputs.RegisterPayload.__name__ == "RegisterPayload"


# ===========================================================================
# Commit 3 - login persistence-safe across Django and Channels HTTP
# ===========================================================================
#
# These package tests own the login rows a live fakeshop `/graphql/` request
# cannot drive: the backend matrix (custom AUTHENTICATION_BACKENDS cannot be
# swapped on the shared aggregate schema mid-request), the post-authentication /
# pre-persistence failure-injection rows (Stage 0 induction mechanisms - real
# raising signal receivers and real SessionStore subclasses whose create / save /
# delete raise; the one justified mock is payload construction), the WebSocket
# login rejection, and the real Channels HTTP round trip + rotation branches.
# The four Django HTTP rotation branches live in the live
# `examples/fakeshop/test_query/test_auth_api.py` per the live-first mandate.

_BACKEND_MODULE = "tests.auth.test_mutations"
_MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"

_LOGIN_VAR_Q = (
    "mutation($u: String!, $p: String!){ login(username: $u, password: $p){ "
    "node{ username } errors{ field messages } } }"
)


class _RecordingBackend:
    """Records every ``(username, password)`` seen; authenticates no one (reach probe)."""

    seen: list = []

    def authenticate(self, request, username=None, password=None, **kwargs):
        type(self).seen.append((username, password))
        return None

    def get_user(self, user_id):
        return None


class _CountingModelBackend(ModelBackend):
    """A real ``ModelBackend`` that counts its ``authenticate`` calls (WS-reject probe)."""

    calls = 0

    def authenticate(self, request, username=None, password=None, **kwargs):
        type(self).calls += 1
        return super().authenticate(request, username=username, password=password, **kwargs)


class _PermissionDeniedBackend:
    """A backend that raises ``PermissionDenied`` (stops backend iteration upstream)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        raise PermissionDenied

    def get_user(self, user_id):
        return None


class _CrashingBackend:
    """A backend whose ``authenticate`` raises a non-``PermissionDenied`` error."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        raise RuntimeError("backend boom")

    def get_user(self, user_id):
        return None


class _AllowInactiveBackend:
    """A custom backend that honors an inactive user (no framework ``is_active`` rule)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_model().objects.filter(username=username).first()
        if user is not None and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        return get_user_model().objects.filter(pk=user_id).first()


class _CycleCreateRaises(DBSessionStore):
    """A real DB session store whose ``create`` raises (session cycle/flush outage)."""

    def create(self):
        raise OSError("session store create failed")


class _ExplicitSaveRaises(DBSessionStore):
    """A real DB store whose UPDATE ``save`` raises but ``create`` (must_create) works.

    ``cycle_key`` uses ``save(must_create=True)`` (permitted here); the resolver's
    explicit ``request.session.save()`` uses ``save(must_create=False)`` (rejected),
    isolating the explicit-save failure row from the cycle row.
    """

    def save(self, must_create=False):
        if not must_create:
            raise OSError("explicit session save failed")
        return super().save(must_create=must_create)


class _DeleteRaises(DBSessionStore):
    """A real DB store whose ``delete`` raises (compensation ``flush`` fails)."""

    def delete(self, session_key=None):
        raise OSError("session delete failed")


def _request_with_store(store):
    """A Django request wired to an explicit session store, anonymous actor."""
    request = RequestFactory().post("/graphql/")
    request.session = store
    request.user = AnonymousUser()
    return request


def _login_exec(
    schema,
    request,
    *,
    username="staff_1",
    password=TEST_USER_PASSWORD,
):
    return schema.execute_sync(
        _LOGIN_VAR_Q,
        variable_values={"u": username, "p": password},
        context_value=request,
    )


@contextlib.contextmanager
def _raising_receiver(signal, message):
    """Connect a real ``signal`` receiver that raises ``RuntimeError(message)`` in the block."""

    def _boom(sender, **kwargs):
        raise RuntimeError(message)

    signal.connect(_boom)
    try:
        yield
    finally:
        signal.disconnect(_boom)


def _raising_login_receiver():
    """Connect a real ``user_logged_in`` receiver that raises after the auth keys write."""
    return _raising_receiver(auth_signals.user_logged_in, "login-signal boom")


def _assert_login_fully_compensated(request):
    """Assert a failed login left NO trace: anonymous actor, no auth key, no durable row.

    The full compensation triple the fail-closed Django-HTTP login rows share: the
    local actor is anonymous, the in-memory ``SESSION_KEY`` auth key is cleared, and
    the durable ``Session`` row (a cycled/rotated empty row included) was deleted.
    """
    assert not request.user.is_authenticated
    assert SESSION_KEY not in request.session
    assert Session.objects.count() == 0


# --- Failure-injection rows (Django HTTP) --------------------------------------


@pytest.mark.django_db
def test_login_payload_construction_failure_is_execution_error_session_untouched(monkeypatch):
    """Row 5 (the one justified mock): a payload build after authenticate never mutates the session."""
    create_users(1)
    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    schema = _login_logout_schema()

    def _boom(*args, **kwargs):
        raise RuntimeError("payload construction boom")

    monkeypatch.setattr(mutation_resolvers, "build_payload", _boom)
    request = _request_with_store(DBSessionStore())
    res = _login_exec(schema, request)
    assert res.errors is not None
    # authenticate ran (valid creds), but the pre-mutation build failure means no login.
    _assert_login_fully_compensated(request)


@override_settings(AUTHENTICATION_BACKENDS=[f"{_BACKEND_MODULE}._CrashingBackend"])
@pytest.mark.django_db
def test_login_backend_crash_propagates_and_leaves_session_untouched():
    """Row 4: a backend raising a non-``PermissionDenied`` error propagates, session untouched."""
    create_users(1)
    schema = _login_logout_schema()
    request = _request_with_store(DBSessionStore())
    res = _login_exec(schema, request)
    assert res.errors is not None
    _assert_login_fully_compensated(request)


@override_settings(
    AUTHENTICATION_BACKENDS=[_MODEL_BACKEND, f"{_BACKEND_MODULE}._AllowInactiveBackend"],
)
@pytest.mark.django_db
def test_login_backend_selection_failure_compensates(monkeypatch):
    """Row 6: multi-backend + a stripped ``user.backend`` -> login-time ``ValueError`` + compensation.

    ``authenticate`` always annotates ``user.backend``; the annotation is removed
    test-side (real-object manipulation, per Stage 0) after a REAL authenticate so
    ``_get_backend_from_user`` raises. The cycle already persisted an empty row; the
    compensating flush deletes it and the actor stays anonymous.
    """
    create_users(1)
    real_authenticate = auth_mutations.auth.authenticate

    def _strip_backend(request, **kwargs):
        user = real_authenticate(request, **kwargs)
        if user is not None and hasattr(user, "backend"):
            del user.backend
        return user

    monkeypatch.setattr(auth_mutations.auth, "authenticate", _strip_backend)
    schema = _login_logout_schema()
    request = _request_with_store(DBSessionStore())
    res = _login_exec(schema, request)
    assert res.errors is not None
    assert not request.user.is_authenticated
    assert Session.objects.count() == 0  # the cycled empty row was flushed


@pytest.mark.django_db
def test_login_session_cycle_failure_keeps_actor_anonymous_and_surfaces_original():
    """Row 7: a session-store outage during rotation -> no success, actor anonymous, error observable."""
    create_users(1)
    schema = _login_logout_schema()
    request = _request_with_store(_CycleCreateRaises())
    res = _login_exec(schema, request)
    assert res.errors is not None
    assert isinstance(res.errors[0].original_error, OSError)
    assert "create failed" in str(res.errors[0].original_error)
    assert not request.user.is_authenticated
    assert Session.objects.count() == 0


@pytest.mark.django_db
def test_login_signal_failure_compensates_in_memory_and_durable():
    """Row 8: a raising ``user_logged_in`` receiver -> compensation clears keys AND deletes the durable row.

    The receiver fires AFTER the auth keys are written in memory and after the
    durable rotated/empty row exists (Stage 0). Compensation must undo BOTH.
    """
    create_users(1)
    schema = _login_logout_schema()
    request = _request_with_store(DBSessionStore())
    with _raising_login_receiver():
        res = _login_exec(schema, request)
    assert res.errors is not None
    _assert_login_fully_compensated(request)


@pytest.mark.django_db
def test_login_explicit_save_failure_compensates():
    """Row 9: the explicit in-resolver ``save`` failing -> compensation, no candidate actor remains."""
    create_users(1)
    schema = _login_logout_schema()
    request = _request_with_store(_ExplicitSaveRaises())
    res = _login_exec(schema, request)
    assert res.errors is not None
    _assert_login_fully_compensated(request)


@pytest.mark.django_db
def test_login_cleanup_failure_retains_primary_and_chains_cleanup():
    """Row 12: a raising signal (primary) + a raising ``delete`` (cleanup) -> primary retained, cleanup chained."""
    create_users(1)
    schema = _login_logout_schema()
    request = _request_with_store(_DeleteRaises())
    with _raising_login_receiver():
        res = _login_exec(schema, request)
    assert res.errors is not None
    primary = res.errors[0].original_error
    assert isinstance(primary, RuntimeError)
    assert "login-signal boom" in str(primary)  # the establishment failure is retained
    assert isinstance(primary.__context__, OSError)  # cleanup chained via PEP 3134
    assert "delete failed" in str(primary.__context__)


# --- Backend matrix (Django HTTP) ---------------------------------------------


@override_settings(
    AUTHENTICATION_BACKENDS=[_MODEL_BACKEND, f"{_BACKEND_MODULE}._AllowInactiveBackend"],
)
@pytest.mark.django_db
def test_backend_order_first_success_wins_model_backend_first():
    """The first compatible backend wins; ``BACKEND_SESSION_KEY`` is that exact backend."""
    create_users(1)
    schema = _login_logout_schema()
    request = _session_request()
    res = _login_exec(schema, request)
    assert res.errors is None, res.errors
    assert res.data["login"]["node"] == {"username": "staff_1"}
    assert request.session[BACKEND_SESSION_KEY] == _MODEL_BACKEND


@override_settings(
    AUTHENTICATION_BACKENDS=[f"{_BACKEND_MODULE}._AllowInactiveBackend", _MODEL_BACKEND],
)
@pytest.mark.django_db
def test_backend_order_first_success_wins_custom_backend_first():
    """Reversing the order changes the persisted backend to the custom one."""
    create_users(1)
    schema = _login_logout_schema()
    request = _session_request()
    res = _login_exec(schema, request)
    assert res.errors is None, res.errors
    assert request.session[BACKEND_SESSION_KEY] == f"{_BACKEND_MODULE}._AllowInactiveBackend"


@override_settings(
    AUTHENTICATION_BACKENDS=[f"{_BACKEND_MODULE}._PermissionDeniedBackend", _MODEL_BACKEND],
)
@pytest.mark.django_db
def test_permission_denied_stops_iteration_and_is_the_standard_envelope():
    """``PermissionDenied`` stops backend iteration -> the byte-identical failed-login envelope."""
    create_users(1)
    schema = _login_logout_schema()
    request = _session_request()
    res = _login_exec(schema, request)
    assert res.errors is None, res.errors
    assert res.data["login"] == {
        "node": None,
        "errors": [{"field": "__all__", "messages": ["Incorrect username/password"]}],
    }


@override_settings(AUTHENTICATION_BACKENDS=[f"{_BACKEND_MODULE}._AllowInactiveBackend"])
@pytest.mark.django_db
def test_custom_backend_authenticating_inactive_user_is_honored():
    """A custom backend may authenticate an inactive user; the framework adds no ``is_active`` rule."""
    create_users(1)
    user = get_user_model().objects.get(username="staff_1")
    user.is_active = False
    user.save()
    schema = _login_logout_schema()
    request = _session_request()
    res = _login_exec(schema, request)
    assert res.errors is None, res.errors
    assert res.data["login"]["node"] == {"username": "staff_1"}


# --- Malformed-credential posture (Django HTTP) -------------------------------


@override_settings(AUTHENTICATION_BACKENDS=[f"{_BACKEND_MODULE}._RecordingBackend"])
@pytest.mark.django_db
@pytest.mark.parametrize(
    "weird",
    [
        "",
        "  spaced  ",
        "with\x00nul",
        "x" * 500,
        "naive-Unicode-\u00fc\u00e9",
    ],
)
def test_storable_weird_credentials_reach_the_backend_unchanged(weird):
    """Storable weird strings are passed to ``authenticate`` verbatim (no trim/normalize/truncate)."""
    create_users(1)
    _RecordingBackend.seen = []
    schema = _login_logout_schema()
    schema.execute_sync(
        _LOGIN_VAR_Q,
        variable_values={"u": weird, "p": weird},
        context_value=_session_request(),
    )
    assert _RecordingBackend.seen == [(weird, weird)]


@override_settings(AUTHENTICATION_BACKENDS=[f"{_BACKEND_MODULE}._RecordingBackend"])
@pytest.mark.django_db
def test_wrong_graphql_type_fails_validation_before_the_resolver():
    """A non-``String`` username fails GraphQL validation; the resolver (and backend) never run."""
    create_users(1)
    _RecordingBackend.seen = []
    schema = _login_logout_schema()
    res = schema.execute_sync(
        'mutation{ login(username: 123, password: "x"){ node{ username } errors{ field } } }',
        context_value=_session_request(),
    )
    assert res.errors is not None
    assert _RecordingBackend.seen == []


@pytest.mark.django_db
def test_login_password_never_appears_in_logs_or_error_text(caplog):
    """The password never leaks into captured logs or exception/repr text (a wrong-password attempt)."""
    create_users(1)
    schema = _login_logout_schema()
    secret = "sup3r-secret-verboten-42"
    with caplog.at_level(logging.DEBUG):
        res = schema.execute_sync(
            _LOGIN_VAR_Q,
            variable_values={"u": "staff_1", "p": secret},
            context_value=_session_request(),
        )
    assert res.data["login"]["node"] is None
    assert secret not in caplog.text
    for error in res.errors or []:
        assert secret not in str(error)


# --- WebSocket login rejection (before authenticate) --------------------------


class _StubContext:
    def __init__(self, request):
        self.request = request


class _StubInfo:
    def __init__(self, request):
        self.context = _StubContext(request)


@override_settings(AUTHENTICATION_BACKENDS=[f"{_BACKEND_MODULE}._CountingModelBackend"])
@pytest.mark.django_db
def test_websocket_login_is_rejected_before_authenticate_is_called():
    """A WebSocket login raises the actionable error BEFORE any ``authenticate`` call."""
    create_users(1)
    _CountingModelBackend.calls = 0
    _login_logout_schema()
    holder = _declared_auth_surface("login")
    adapter = _channels_adapter("websocket")
    with pytest.raises(ConfigurationError, match="WebSocket"):
        auth_mutations._login_resolve_body(
            holder,
            _StubInfo(adapter),
            username="staff_1",
            password=TEST_USER_PASSWORD,
        )
    assert _CountingModelBackend.calls == 0


# --- Channels HTTP round trip + rotation (real HttpCommunicator) --------------

_CH_LOGIN = (
    "mutation($u: String!, $p: String!){ login(username: $u, password: $p){ "
    "node{ username } errors{ field } } }"
)
_CH_ME = "{ me{ username } }"


def _auth_router_schema():
    """Declare UserT + login/logout/me and return a finalized DjangoSchema (Query carries ``me``).

    The ``me`` field is built here (per call, inside the test's cleared registry) and
    seamed into ``_login_logout_schema`` via ``query_type`` so the shared UserT
    declaration + login/logout Mutation + finalize are not re-spelled.
    """

    @strawberry.type
    class Query:
        me = current_user()

    return _login_logout_schema(query_type=Query)


def _channels_router(schema):
    from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

    return DjangoGraphQLProtocolRouter(schema)


async def _ch_post(
    router,
    query,
    variables=None,
    cookie=None,
):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
        (b"host", b"testserver"),
    ]
    if cookie is not None:
        headers.append((b"cookie", cookie.encode()))
    communicator = HttpCommunicator(router, "POST", "/graphql", body=body, headers=headers)
    return await communicator.get_response(timeout=10)


def _set_cookie(response):
    for name, value in response["headers"]:
        if name.lower() == b"set-cookie":
            return value.decode().split(";")[0]
    return None


def _cookie_key(cookie):
    return cookie.split("=", 1)[1]


def _open_store(key=None):
    import importlib

    return importlib.import_module(settings.SESSION_ENGINE).SessionStore(key)


def _seed_session(**data):
    store = _open_store()
    for key, value in data.items():
        store[key] = value
    store.save()
    return store.session_key


def _read_session(key, field):
    return _open_store(key).get(field)


def _write_session(key, **data):
    store = _open_store(key)
    for name, value in data.items():
        store[name] = value
    store.save()


def _change_password(username, password):
    user = get_user_model().objects.get(username=username)
    user.set_password(password)
    user.save()


@pytest.mark.django_db(transaction=True)
async def test_channels_http_login_round_trip_sets_cookie_keys_and_authenticates():
    """A real Channels ``HttpCommunicator`` login: Set-Cookie, stored keys/backend, authed follow-up."""
    await _acreate_users(1)
    router = _channels_router(_auth_router_schema())
    resp = await _ch_post(router, _CH_LOGIN, {"u": "staff_1", "p": TEST_USER_PASSWORD})
    assert resp["status"] == 200
    body = json.loads(resp["body"])
    assert body.get("errors") is None, body
    assert body["data"]["login"]["node"] == {"username": "staff_1"}
    cookie = _set_cookie(resp)
    assert cookie is not None
    assert cookie.startswith(f"{settings.SESSION_COOKIE_NAME}=")
    key = _cookie_key(cookie)
    stored_pk = await database_sync_to_async(_read_session)(key, SESSION_KEY)
    stored_backend = await database_sync_to_async(_read_session)(key, BACKEND_SESSION_KEY)
    assert stored_pk is not None
    assert stored_backend == _MODEL_BACKEND
    follow_up = await _ch_post(router, _CH_ME, cookie=cookie)
    assert json.loads(follow_up["body"])["data"]["me"] == {"username": "staff_1"}


@pytest.mark.django_db(transaction=True)
async def test_channels_http_login_anon_to_auth_cycles_key_and_preserves_data():
    """Rotation branch 1 (Channels HTTP): cycle the key, keep anonymous data."""
    await _acreate_users(1)
    router = _channels_router(_auth_router_schema())
    anon_key = await database_sync_to_async(_seed_session)(cart=["item-1"])
    cookie = f"{settings.SESSION_COOKIE_NAME}={anon_key}"
    resp = await _ch_post(
        router,
        _CH_LOGIN,
        {"u": "staff_1", "p": TEST_USER_PASSWORD},
        cookie=cookie,
    )
    new_key = _cookie_key(_set_cookie(resp))
    assert new_key != anon_key
    assert await database_sync_to_async(_read_session)(new_key, "cart") == ["item-1"]
    assert await database_sync_to_async(_read_session)(new_key, SESSION_KEY) is not None


@pytest.mark.django_db(transaction=True)
async def test_channels_http_login_as_different_user_flushes_old_data():
    """Rotation branch 2 (Channels HTTP): a different user flushes old data + new key."""
    await _acreate_users(1)
    router = _channels_router(_auth_router_schema())
    r1 = await _ch_post(router, _CH_LOGIN, {"u": "staff_1", "p": TEST_USER_PASSWORD})
    cookie_a = _set_cookie(r1)
    key_a = _cookie_key(cookie_a)
    await database_sync_to_async(_write_session)(key_a, scratch="staff-1-data")
    r2 = await _ch_post(
        router,
        _CH_LOGIN,
        {"u": "regular_1", "p": TEST_USER_PASSWORD},
        cookie=cookie_a,
    )
    key_b = _cookie_key(_set_cookie(r2))
    assert key_b != key_a
    assert await database_sync_to_async(_read_session)(key_b, "scratch") is None


@pytest.mark.django_db(transaction=True)
async def test_channels_http_relogin_same_user_matching_hash_retains_key():
    """Rotation branch 3 (Channels HTTP): same user + matching auth hash keeps the key."""
    await _acreate_users(1)
    router = _channels_router(_auth_router_schema())
    r1 = await _ch_post(router, _CH_LOGIN, {"u": "staff_1", "p": TEST_USER_PASSWORD})
    cookie_a = _set_cookie(r1)
    key_a = _cookie_key(cookie_a)
    r2 = await _ch_post(
        router,
        _CH_LOGIN,
        {"u": "staff_1", "p": TEST_USER_PASSWORD},
        cookie=cookie_a,
    )
    assert _cookie_key(_set_cookie(r2)) == key_a


@pytest.mark.django_db(transaction=True)
async def test_channels_http_relogin_same_user_mismatched_hash_flushes_and_replaces():
    """Rotation branch 4 (Channels HTTP): same user + mismatched auth hash flush+replace."""
    await _acreate_users(1)
    router = _channels_router(_auth_router_schema())
    r1 = await _ch_post(router, _CH_LOGIN, {"u": "staff_1", "p": TEST_USER_PASSWORD})
    cookie_a = _set_cookie(r1)
    key_a = _cookie_key(cookie_a)
    await database_sync_to_async(_change_password)("staff_1", "correct-horse-9battery")
    r2 = await _ch_post(
        router,
        _CH_LOGIN,
        {"u": "staff_1", "p": "correct-horse-9battery"},
        cookie=cookie_a,
    )
    assert _cookie_key(_set_cookie(r2)) != key_a


# --- Post-login last_login exposure (security invariant 3) --------------------


def _login_schema_with_last_login():
    """Declare the ``last_login``-exposing UserT + a login/logout Mutation; finalize."""
    return _login_logout_schema(
        declare=lambda: _declare_user_type(fields=("id", "username", "last_login")),
    )


_LOGIN_LAST_LOGIN_Q = (
    "mutation($u: String!, $p: String!){ login(username: $u, password: $p){ "
    "node{ username lastLogin } errors{ field } } }"
)


@pytest.mark.django_db
def test_sync_login_payload_exposes_the_post_login_last_login():
    """Invariant 3: the prebuilt payload holds the user OBJECT, so ``lastLogin`` reflects the signal.

    A user seeded with ``last_login=None`` (never logged in) whose login response's
    nested ``lastLogin`` resolves non-null pins that the payload container exposes the
    POST-login user mutated by Django's ``user_logged_in`` receiver
    (``update_last_login``), not a pre-login scalar snapshot.
    """
    create_users(1)
    User.objects.filter(username="staff_1").update(last_login=None)
    schema = _login_schema_with_last_login()
    request = _session_request()
    res = schema.execute_sync(
        _LOGIN_LAST_LOGIN_Q,
        variable_values={"u": "staff_1", "p": TEST_USER_PASSWORD},
        context_value=request,
    )
    assert res.errors is None, res.errors
    node = res.data["login"]["node"]
    assert node["username"] == "staff_1"
    assert node["lastLogin"] is not None  # advanced by the post-login signal


@pytest.mark.django_db
async def test_async_login_payload_exposes_the_post_login_last_login():
    """The async twin: the Django HTTP async body bridges to the sync body, same guarantee."""
    await _acreate_users(1)
    await database_sync_to_async(User.objects.filter(username="staff_1").update)(last_login=None)
    schema = _login_schema_with_last_login()
    request = _session_request()
    res = await schema.execute(
        _LOGIN_LAST_LOGIN_Q,
        variable_values={"u": "staff_1", "p": TEST_USER_PASSWORD},
        context_value=request,
    )
    assert res.errors is None, res.errors
    node = res.data["login"]["node"]
    assert node["username"] == "staff_1"
    assert node["lastLogin"] is not None


# --- SyncGraphQLHTTPConsumer sync bridge (the async_to_sync arm) --------------


@pytest.mark.django_db(transaction=True)
def test_sync_channels_http_bridge_establishes_and_persists_the_session():
    """The ``transport is CHANNELS_HTTP`` arm of the SYNC body: one ``async_to_sync`` bridge.

    Drives ``_login_resolve_body`` directly over a Channels HTTP scope adapter (the
    directly-invoked Strawberry ``SyncGraphQLHTTPConsumer`` shape) under synchronous
    execution, so the sole ``async_to_sync(_channels_http_login_establish)`` hop runs.
    Asserts the success payload holds the authenticated user object, the scope actor is
    authenticated, and the session is DURABLY persisted (a ``Session`` row carrying both
    auth keys), per the transport contract's Channels persistence rule.
    """
    create_users(1)
    _login_logout_schema()
    holder = _declared_auth_surface("login")
    adapter = _channels_adapter()
    payload = auth_mutations._login_resolve_body(
        holder,
        _StubInfo(adapter),
        username="staff_1",
        password=TEST_USER_PASSWORD,
    )
    assert payload.errors == []
    assert payload.node.username == "staff_1"  # the success payload holds the user object
    assert adapter.scope["user"].is_authenticated
    session = adapter.scope["session"]
    assert session[SESSION_KEY] is not None
    assert session[BACKEND_SESSION_KEY] == _MODEL_BACKEND
    stored = Session.objects.get(session_key=session.session_key)  # durable row exists
    decoded = stored.get_decoded()
    assert decoded[SESSION_KEY] == session[SESSION_KEY]
    assert decoded[BACKEND_SESSION_KEY] == _MODEL_BACKEND


# --- Channels HTTP login failure injection (fail closed) ----------------------


@pytest.mark.django_db(transaction=True)
async def test_channels_http_login_signal_failure_compensates_scope_and_durable():
    """The Channels twin of the login-signal row: a raising ``user_logged_in`` receiver.

    Drives ``_channels_http_login_establish`` directly over a Channels HTTP scope. The
    receiver fires inside ``channels.auth.login`` (after the rotated/empty durable row
    exists), so establishment raises before the success payload. Compensation makes the
    scope actor anonymous and ``aflush`` deletes the durable row; the original error
    surfaces (no false clean-state claim, no success).
    """
    await _acreate_users(1)
    user = await get_user_model().objects.aget(username="staff_1")
    store = DBSessionStore()
    adapter = _channels_adapter(store=store)
    with _raising_login_receiver(), pytest.raises(RuntimeError, match="login-signal boom"):
        await auth_mutations._channels_http_login_establish(adapter, store, user)
    assert isinstance(adapter.scope["user"], AnonymousUser)  # scope actor made anonymous
    assert await Session.objects.acount() == 0  # durable rotated row deleted


@pytest.mark.django_db(transaction=True)
async def test_channels_http_login_cleanup_failure_retains_primary_and_chains_cleanup():
    """The Channels twin of the cleanup-failure row: establishment AND ``aflush`` raise.

    A raising ``user_logged_in`` receiver (primary) plus a store whose ``delete`` raises
    (the compensating ``aflush`` fails). The ORIGINAL establishment error is retained and
    the cleanup failure chains via ``__context__`` (PEP 3134) - never a false clean state.
    """
    await _acreate_users(1)
    user = await get_user_model().objects.aget(username="staff_1")

    class _AsyncDeleteRaises(DBSessionStore):
        """A real DB store whose async ``adelete`` raises (the ``aflush`` cleanup fails)."""

        async def adelete(self, session_key=None):
            raise OSError("async session delete failed")

    store = _AsyncDeleteRaises()
    adapter = _channels_adapter(store=store)
    with (
        _raising_login_receiver(),
        pytest.raises(RuntimeError, match="login-signal boom") as excinfo,
    ):
        await auth_mutations._channels_http_login_establish(adapter, store, user)
    primary = excinfo.value
    assert isinstance(primary.__context__, OSError)  # cleanup chained via PEP 3134
    assert "async session delete failed" in str(primary.__context__)


@pytest.mark.django_db(transaction=True)
async def test_channels_http_login_cancelled_between_key_write_and_asave_compensates():
    """A ``CancelledError`` injected between the Channels key-write and ``asave``.

    Compensation must cover ``BaseException`` (not just ``Exception``) so a task
    cancellation landing after ``channels.auth.login`` wrote the rotated durable row
    but at the explicit ``asave`` still fails closed: the scope actor is reset to
    ``AnonymousUser`` and ``aflush`` deletes the rotated row, and the
    ``CancelledError`` propagates (never swallowed, never a false clean state).
    """
    await _acreate_users(1)
    user = await get_user_model().objects.aget(username="staff_1")

    class _AsaveCancelled(DBSessionStore):
        """A real DB store whose explicit ``asave`` raises ``CancelledError``."""

        async def asave(self, must_create=False):
            raise asyncio.CancelledError

    store = _AsaveCancelled()
    adapter = _channels_adapter(store=store)
    with pytest.raises(asyncio.CancelledError):
        await auth_mutations._channels_http_login_establish(adapter, store, user)
    assert isinstance(adapter.scope["user"], AnonymousUser)  # scope actor made anonymous
    assert await Session.objects.acount() == 0  # durable rotated row flushed


@pytest.mark.django_db(transaction=True)
async def test_async_channels_http_wrong_password_is_failed_login_envelope_session_untouched():
    """The failed-auth arm of the native ASYNC body over a Channels HTTP scope.

    A wrong password through ``_login_resolve_body_async`` on a classified Channels HTTP
    scope returns the standard undifferentiated failed-login envelope BEFORE any session
    mutation - no durable row is written.
    """
    await _acreate_users(1)
    _login_logout_schema()
    holder = _declared_auth_surface("login")
    adapter = _channels_adapter()
    payload = await auth_mutations._login_resolve_body_async(
        holder,
        _StubInfo(adapter),
        username="staff_1",
        password="not-the-password",
    )
    assert payload.node is None
    assert [(e.field, e.messages) for e in payload.errors] == [
        ("__all__", ["Incorrect username/password"]),
    ]
    assert isinstance(adapter.scope["user"], AnonymousUser)  # session untouched
    assert await Session.objects.acount() == 0


# --- Enumeration guard: one byte-identical envelope across failure classes ----


@pytest.mark.django_db
def test_all_four_failure_classes_share_one_byte_identical_envelope():
    """Wrong-password, unknown-user, inactive-under-``ModelBackend``, and backend ``PermissionDenied``.

    The same selection set over all four failure classes must yield ``==`` full
    GraphQL responses (the account-enumeration guard: ``field: "__all__"`` + the one
    undifferentiated message, no top-level error, for every class).
    """
    create_users(1)
    schema = _login_logout_schema()

    def _envelope(variables, backends=None):
        ctx = (
            override_settings(AUTHENTICATION_BACKENDS=backends)
            if backends is not None
            else contextlib.nullcontext()
        )
        with ctx:
            res = schema.execute_sync(
                _LOGIN_VAR_Q,
                variable_values=variables,
                context_value=_session_request(),
            )
        return {"data": res.data, "errors": res.errors}

    User.objects.filter(username="regular_1").update(is_active=False)
    wrong_password = _envelope({"u": "staff_1", "p": "not-the-password"})
    unknown_user = _envelope({"u": "no-such-user", "p": TEST_USER_PASSWORD})
    inactive = _envelope({"u": "regular_1", "p": TEST_USER_PASSWORD})
    permission_denied = _envelope(
        {"u": "staff_1", "p": TEST_USER_PASSWORD},
        backends=[f"{_BACKEND_MODULE}._PermissionDeniedBackend", _MODEL_BACKEND],
    )
    assert wrong_password == unknown_user == inactive == permission_denied
    assert wrong_password == {
        "data": {
            "login": {
                "node": None,
                "errors": [{"field": "__all__", "messages": ["Incorrect username/password"]}],
            },
        },
        "errors": None,
    }


# --- Django HTTP: the session stays modified so the cookie is emitted ---------


@pytest.mark.django_db
def test_sync_django_http_login_leaves_session_modified_for_the_cookie():
    """Transport contract: a successful Django HTTP login leaves ``session.modified`` set.

    The middleware-still-emits-the-rotated-cookie observable - the resolver's explicit
    ``save()`` does NOT clear the flag, so ``SessionMiddleware`` saves again and sends
    the cookie transition that makes the durable session usable by the client.
    """
    create_users(1)
    schema = _login_logout_schema()
    request = _session_request()
    res = _login_exec(schema, request)
    assert res.errors is None, res.errors
    assert res.data["login"]["node"] == {"username": "staff_1"}
    assert request.session.modified is True


# ===========================================================================
# Commit 4 - logout durable and fail-closed on every supported transport
# ===========================================================================
#
# These package tests own the logout rows a live fakeshop `/graphql/` request
# cannot drive: the Channels HTTP round trip + anonymous residue flush (real
# HttpCommunicator), the real WebSocket server-side logout + reconnect-with-old-cookie
# invalidation, the signed-cookie WebSocket rejection before mutation, and the
# post-capture failure-injection rows (Stage 0 induction mechanisms - a real raising
# `user_logged_out` receiver and a real SessionStore subclass whose `delete` raises)
# on BOTH the Django HTTP and Channels paths. The Django HTTP authenticated/anonymous
# round trip lives in the live `examples/fakeshop/test_query/test_auth_api.py`.

_CH_LOGOUT = "mutation{ logout{ ok errors{ field } } }"


class _FlushRecordingStore(DBSessionStore):
    """A real DB store that counts ``flush`` calls (the signed-cookie WS reject probe)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flush_calls = 0

    def flush(self):
        self.flush_calls += 1
        return super().flush()


def _raising_logout_receiver():
    """Connect a real ``user_logged_out`` receiver that raises before the flush."""
    return _raising_receiver(auth_signals.user_logged_out, "logout-signal boom")


def _session_row_exists(key):
    return Session.objects.filter(session_key=key).exists()


def _logout_payload_cls():
    """Build the login/logout schema and return the bound ``LogoutPayload`` class."""
    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    _login_logout_schema()
    return mutation_resolvers.payload_cls_for(_declared_auth_surface("logout"))


def _establish_authenticated_django_session(user, store):
    """Log ``user`` into ``store`` on a real Django request (a durable authed row)."""
    request = RequestFactory().post("/graphql/")
    request.session = store
    request.user = AnonymousUser()
    auth_mutations.auth.login(request, user)
    request.session.save()
    return request


# --- Django HTTP failure injection (fail closed) ------------------------------


@pytest.mark.django_db
def test_django_logout_signal_failure_no_ok_and_actor_anonymized():
    """Logout row: a raising ``user_logged_out`` receiver -> no ok, actor anonymous.

    The receiver fires BEFORE ``flush`` (Stage 0), so the durable row is NOT
    invalidated - and the resolver never falsely claims it was (no ok payload; the
    error propagates as a top-level GraphQL error).
    """
    create_users(1)
    schema = _login_logout_schema()
    user = get_user_model().objects.get(username="staff_1")
    request = _establish_authenticated_django_session(user, DBSessionStore())
    key = request.session.session_key
    assert _session_row_exists(key)
    with _raising_logout_receiver():
        res = schema.execute_sync(_LOGOUT_Q, context_value=request)
    assert res.errors is not None
    assert not request.user.is_authenticated  # local actor made anonymous
    assert _session_row_exists(key)  # signal preceded flush; no false invalidation


@pytest.mark.django_db
def test_django_logout_flush_failure_no_ok_and_actor_anonymized():
    """Logout row: a store outage during ``flush``/``delete`` -> no ok, actor anonymous, error propagates."""
    create_users(1)
    schema = _login_logout_schema()
    user = get_user_model().objects.get(username="staff_1")
    request = _establish_authenticated_django_session(user, _DeleteRaises())
    res = schema.execute_sync(_LOGOUT_Q, context_value=request)
    assert res.errors is not None
    assert isinstance(res.errors[0].original_error, OSError)
    assert "delete failed" in str(res.errors[0].original_error)
    assert not request.user.is_authenticated


# --- Channels failure injection (fail closed) ---------------------------------


@pytest.mark.django_db(transaction=True)
async def test_channels_logout_flush_failure_no_ok_and_scope_anonymized():
    """The Channels twin: a ``delete`` outage -> no ok payload, scope actor anonymized."""
    await _acreate_users(1)
    payload_cls = await database_sync_to_async(_logout_payload_cls)()
    user = await get_user_model().objects.aget(username="staff_1")
    store = _DeleteRaises()

    def _seed(store):
        store["scratch"] = "durable"
        store.save()

    await database_sync_to_async(_seed)(store)
    adapter = _channels_adapter(store=store, user=user)
    with pytest.raises(OSError, match="delete failed"):
        await auth_mutations._channels_logout(adapter, payload_cls)
    assert isinstance(adapter.scope["user"], AnonymousUser)


@pytest.mark.django_db(transaction=True)
async def test_channels_logout_signal_failure_no_ok_and_scope_anonymized():
    """The Channels twin: a raising ``user_logged_out`` receiver -> no ok, scope actor anonymized."""
    await _acreate_users(1)
    payload_cls = await database_sync_to_async(_logout_payload_cls)()
    user = await get_user_model().objects.aget(username="staff_1")
    adapter = _channels_adapter(user=user)
    with _raising_logout_receiver(), pytest.raises(RuntimeError, match="logout-signal boom"):
        await auth_mutations._channels_logout(adapter, payload_cls)
    assert isinstance(adapter.scope["user"], AnonymousUser)


# --- Signed-cookie WebSocket logout rejection (before mutation) ---------------


@override_settings(SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies")
@pytest.mark.django_db
def test_websocket_signed_cookie_logout_rejected_before_any_mutation():
    """A signed-cookie WebSocket logout raises the actionable error, session untouched.

    The rejection fires in the prologue, BEFORE ``require_session``, the gate, or any
    teardown, so the recording store's ``flush`` is never called and the scope actor
    is unchanged.
    """
    create_users(1)
    _login_logout_schema()
    holder = _declared_auth_surface("logout")
    user = get_user_model().objects.get(username="staff_1")
    store = _FlushRecordingStore()
    adapter = _channels_adapter("websocket", store=store, user=user)
    with pytest.raises(ConfigurationError, match="signed-cookie WebSocket"):
        auth_mutations._logout_resolve_body(holder, _StubInfo(adapter))
    assert store.flush_calls == 0  # no mutation reached
    assert adapter.scope["user"] is user  # actor unchanged


# --- SyncGraphQLHTTPConsumer logout bridge (the async_to_sync arm) ------------


@pytest.mark.django_db(transaction=True)
def test_sync_channels_http_logout_bridge_tears_down_the_session():
    """The ``transport is CHANNELS_HTTP`` arm of the SYNC logout body: one ``async_to_sync`` bridge.

    Drives ``_logout_resolve_body`` directly over a Channels HTTP scope adapter (the
    directly-invoked Strawberry ``SyncGraphQLHTTPConsumer`` shape) under synchronous
    execution, so the sole ``async_to_sync(_channels_logout)`` hop runs. Asserts the
    ok payload (an authenticated actor existed under the lock), the scope actor is
    anonymized, and the native flush durably deleted the session row.
    """
    create_users(1)
    _login_logout_schema()
    holder = _declared_auth_surface("logout")
    user = get_user_model().objects.get(username="staff_1")
    store = DBSessionStore()
    store["scratch"] = "must-be-flushed"
    store.save()
    key = store.session_key
    adapter = _channels_adapter(store=store, user=user)
    payload = auth_mutations._logout_resolve_body(holder, _StubInfo(adapter))
    assert payload.ok is True
    assert payload.errors == []
    assert isinstance(adapter.scope["user"], AnonymousUser)
    assert not _session_row_exists(key)  # the native flush deleted the durable row


# --- Channels HTTP logout round trip (real HttpCommunicator) ------------------


@pytest.mark.django_db(transaction=True)
async def test_channels_http_logout_invalidates_cookie_and_durable_session():
    """A real Channels ``HttpCommunicator`` logout: ok, emptied Set-Cookie, deleted row, anon follow-up."""
    await _acreate_users(1)
    router = _channels_router(_auth_router_schema())
    login = await _ch_post(router, _CH_LOGIN, {"u": "staff_1", "p": TEST_USER_PASSWORD})
    cookie = _set_cookie(login)
    key = _cookie_key(cookie)
    assert await database_sync_to_async(_session_row_exists)(key)

    resp = await _ch_post(router, _CH_LOGOUT, cookie=cookie)
    assert resp["status"] == 200
    body = json.loads(resp["body"])
    assert body.get("errors") is None, body
    assert body["data"]["logout"] == {"ok": True, "errors": []}
    # The durable server-side row is gone and the browser cookie is emptied.
    assert not await database_sync_to_async(_session_row_exists)(key)
    set_cookie = _set_cookie(resp)
    assert set_cookie is not None
    assert _cookie_key(set_cookie).strip('"') == ""  # deleted/emptied Set-Cookie
    # The OLD cookie can no longer authenticate a follow-up request.
    follow_up = await _ch_post(router, _CH_ME, cookie=cookie)
    assert json.loads(follow_up["body"])["data"]["me"] is None


@pytest.mark.django_db(transaction=True)
async def test_channels_http_anonymous_logout_is_false_but_flushes_residue():
    """Anonymous Channels HTTP logout returns ok:false while still flushing residual data."""
    await _acreate_users(1)
    router = _channels_router(_auth_router_schema())
    anon_key = await database_sync_to_async(_seed_session)(cart=["item-1"])
    cookie = f"{settings.SESSION_COOKIE_NAME}={anon_key}"
    resp = await _ch_post(router, _CH_LOGOUT, cookie=cookie)
    body = json.loads(resp["body"])
    assert body.get("errors") is None, body
    assert body["data"]["logout"] == {"ok": False, "errors": []}
    # Residual anonymous data is flushed durably even though ok is false.
    assert not await database_sync_to_async(_session_row_exists)(anon_key)
    assert await database_sync_to_async(_read_session)(anon_key, "cart") is None


# --- WebSocket server-side logout + reconnect invalidation (real communicator) --


async def _ws_open(router, cookie=None):
    """Open a graphql-transport-ws socket and complete connection_init/ack."""
    headers = [(b"origin", b"http://testserver")]
    if cookie is not None:
        headers.append((b"cookie", cookie.encode()))
    communicator = WebsocketCommunicator(
        router,
        "/graphql",
        headers=headers,
        subprotocols=["graphql-transport-ws"],
    )
    connected, protocol = await communicator.connect(timeout=10)
    assert connected, "websocket handshake failed"
    assert protocol == "graphql-transport-ws"
    await communicator.send_json_to({"type": "connection_init"})
    ack = await communicator.receive_json_from(timeout=10)
    assert ack["type"] == "connection_ack", ack
    return communicator


async def _ws_run(communicator, query, op_id):
    """Run one single-result operation, draining the ``next`` and ``complete`` frames."""
    await communicator.send_json_to(
        {"type": "subscribe", "id": op_id, "payload": {"query": query}},
    )
    msg = await communicator.receive_json_from(timeout=10)
    assert msg["type"] == "next", msg
    complete = await communicator.receive_json_from(timeout=10)
    assert complete["type"] == "complete", complete
    payload = msg["payload"]
    assert payload.get("errors") is None, payload
    return payload["data"]


@pytest.mark.django_db(transaction=True)
async def test_websocket_server_side_logout_invalidates_and_survives_reconnect():
    """Real WebSocket logout: ok, same-socket ``me`` null, durable row gone, reconnect anonymous."""
    await _acreate_users(1)
    router = _channels_router(_auth_router_schema())
    # Authenticate via a cookie from a prior HTTP login (WS login is unsupported).
    login = await _ch_post(router, _CH_LOGIN, {"u": "staff_1", "p": TEST_USER_PASSWORD})
    cookie = _set_cookie(login)
    key = _cookie_key(cookie)

    communicator = await _ws_open(router, cookie=cookie)
    try:
        assert (await _ws_run(communicator, _CH_ME, "1"))["me"] == {"username": "staff_1"}
        assert (await _ws_run(communicator, _CH_LOGOUT, "2"))["logout"] == {
            "ok": True,
            "errors": [],
        }
        # The same socket now sees the anonymous actor.
        assert (await _ws_run(communicator, _CH_ME, "3"))["me"] is None
    finally:
        await communicator.disconnect()

    # The old server-side session record is durably invalidated.
    assert not await database_sync_to_async(_session_row_exists)(key)
    # A NEW connection presenting the OLD cookie is anonymous.
    reconnect = await _ws_open(router, cookie=cookie)
    try:
        assert (await _ws_run(reconnect, _CH_ME, "1"))["me"] is None
    finally:
        await reconnect.disconnect()


# =============================================================================
# Commit 5 -- same-scope auth serialization and race behavior
# =============================================================================
#
# These prove the plan's Concurrent mutation policy: same-scope Channels
# operations are linearized by the ONE scope-owned ``asyncio.Lock`` (security
# invariant 12), and cross-request HTTP session deletion propagates the upstream
# interruption instead of recreating the logged-out session.
#
# Race-driving approach (recorded per the Commit 5 brief): the two multiplexed
# WebSocket races drive the resolver bodies (``_channels_logout`` /
# ``_login_resolve_body_async``) directly over ONE shared scope adapter rather
# than pushing two frames through the real graphql-transport-ws consumer. Frame
# interleaving through the consumer is not deterministically controllable:
# ``channels.auth.logout`` runs its whole teardown inside a single
# ``database_sync_to_async`` thread, so there is no in-teardown seam the consumer
# exposes for a barrier, and the consumer serializes its own inbound frames on its
# per-connection dispatch. Driving the bodies lets a real ``SessionStore``
# subclass (a threading-barrier ``flush``) park operation 1 mid-teardown WHILE it
# holds the scope lock, so "operation 2 is provably blocked behind it" becomes a
# fact about the lock's own waiter queue -- the deterministic
# ``asyncio.Event``/waiter-drain shape reused from
# ``tests/auth/test_sessions.py::test_scope_lock_serializes_two_operations_on_one_scope``,
# with no wall-clock sleeps.


class _BarrierFlushStore(DBSessionStore):
    """A real DB store whose first ARMED ``flush`` parks on a threading barrier.

    ``channels.auth.logout`` runs its whole teardown (signal, ``flush``, actor
    reset) inside one ``database_sync_to_async`` thread, so this threading barrier
    -- not an ``asyncio.Event`` -- is the seam that parks operation 1 inside its
    critical section while it still holds the scope lock. Only ARMED flushes park
    (the authenticated-session setup flushes/cycles are left untouched), and only
    the first of them, so operation 2's later teardown runs unblocked.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flush_entered = threading.Event()
        self.flush_release = threading.Event()
        self.armed = False
        self.armed_flushes = 0

    def flush(self):
        if self.armed:
            self.armed_flushes += 1
            if self.armed_flushes == 1:
                self.flush_entered.set()
                assert self.flush_release.wait(timeout=10), "barrier flush was never released"
        return super().flush()


def _authed_channels_scope(store, scope_type):
    """Return a scope adapter over ``store`` carrying an authenticated actor.

    ``store`` is logged in on a throwaway Django request first (a durable authed
    row), then wired into a fresh Channels scope of ``scope_type`` alongside the
    same authenticated user, so ``_channels_logout``'s under-lock actor capture
    observes an authenticated actor.
    """
    user = get_user_model().objects.get(username="staff_1")
    _establish_authenticated_django_session(user, store)
    key = store.session_key
    adapter = _channels_adapter(scope_type, store=store, user=user)
    return adapter, user, key


async def _cancel_all(*tasks):
    """Cancel + await every not-done task (``-W error`` orphaned-task hygiene)."""
    for task in tasks:
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


@pytest.mark.django_db(transaction=True)
async def test_two_concurrent_logouts_on_one_scope_serialize_and_delete_once():
    """Two logouts multiplexed on ONE scope serialize: first sees the actor, second anonymous.

    Operation 1 acquires the scope lock and parks inside its native teardown (the
    threading-barrier ``flush``) while holding it. Operation 2 is then provably
    blocked on the SAME scope-owned lock (a waiter is enqueued) before op 1 is
    released. The result: op 1 observed the authenticated actor (``ok: true``), op
    2 observed anonymous state (``ok: false``), the durable row was deleted exactly
    once, and the final scope actor is anonymous -- no same-scope split brain.
    """
    await _acreate_users(1)
    payload_cls = await database_sync_to_async(_logout_payload_cls)()
    store = _BarrierFlushStore()
    adapter, _user, key = await database_sync_to_async(_authed_channels_scope)(store, "http")
    store.armed = True
    assert await database_sync_to_async(_session_row_exists)(key)

    op1 = asyncio.create_task(auth_mutations._channels_logout(adapter, payload_cls))
    try:
        # op 1 is now inside its native teardown, holding the scope lock.
        await _drain_until(store.flush_entered.is_set)
        lock = adapter.scope[_SCOPE_LOCK_KEY]
        assert lock.locked()

        op2 = asyncio.create_task(auth_mutations._channels_logout(adapter, payload_cls))
        try:
            # op 2 is provably parked on the SAME lock's waiter queue behind op 1.
            await _drain_until(lambda: bool(getattr(lock, "_waiters", None)))
            assert not op2.done()  # serialized, not interleaved

            store.flush_release.set()
            payload1 = await op1
            payload2 = await op2

            assert (payload1.ok, payload1.errors) == (True, [])
            assert (payload2.ok, payload2.errors) == (False, [])
            assert isinstance(adapter.scope["user"], AnonymousUser)
            assert not lock.locked()
            assert store.armed_flushes == 2  # both teardowns ran (idempotent)
            # The durable row was deleted exactly once and never recreated.
            assert not await database_sync_to_async(_session_row_exists)(key)
        finally:
            await _cancel_all(op2)
    finally:
        store.flush_release.set()
        await _cancel_all(op1)


@pytest.mark.django_db(transaction=True)
async def test_logout_racing_a_websocket_login_on_one_scope_cannot_revive_it():
    """A WebSocket login racing a logout on one scope is rejected before it can mutate.

    Login over a WebSocket is unsupported and rejected in the prologue, BEFORE
    authentication or any session mutation or lock acquisition, so however it
    interleaves with the concurrent logout it can neither revive nor partially
    mutate the scope. Final state: anonymous actor, durable row gone, no candidate
    auth keys written by the rejected login.
    """
    await _acreate_users(1)
    _login_logout_schema()
    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    logout_payload_cls = await database_sync_to_async(mutation_resolvers.payload_cls_for)(
        _declared_auth_surface("logout"),
    )
    login_holder = _declared_auth_surface("login")
    store = DBSessionStore()
    adapter, _user, key = await database_sync_to_async(_authed_channels_scope)(store, "websocket")
    assert await database_sync_to_async(_session_row_exists)(key)

    logout_task = asyncio.create_task(auth_mutations._channels_logout(adapter, logout_payload_cls))
    login_task = asyncio.create_task(
        auth_mutations._login_resolve_body_async(
            login_holder,
            _StubInfo(adapter),
            username="staff_1",
            password=TEST_USER_PASSWORD,
        ),
    )
    try:
        logout_payload = await logout_task
        with pytest.raises(ConfigurationError, match="WebSocket"):
            await login_task

        assert (logout_payload.ok, logout_payload.errors) == (True, [])
        assert isinstance(adapter.scope["user"], AnonymousUser)
        # The rejected login wrote no candidate auth keys and could not recreate.
        assert SESSION_KEY not in store
        assert not await database_sync_to_async(_session_row_exists)(key)
    finally:
        await _cancel_all(logout_task, login_task)


# --- Concurrent cross-request HTTP session deletion (upstream interruption) ----


class _DeleteBeforeExplicitSaveStore(DBSessionStore):
    """A real DB store that fires a callback between login's key-write and the save.

    Models request A logging out (deleting the shared session row) while request B
    is mid-login on the same cookie: the retain-key login path leaves the session
    key in place and the resolver's explicit ``save(must_create=False)`` is the
    persistence step. The callback fires once, immediately before that explicit
    save, sequencing A's delete deterministically between B's key-write and B's
    save -- a real store hook, not a behavior mock.
    """

    # Django's session signing salt is derived from the store class qualname, so a
    # subclass would otherwise fail to decode a row written by DBSessionStore. Pin
    # it back to the base so this store reads the shared seed session's data (and
    # therefore takes the retain-key login path instead of cycling a fresh key).
    key_salt = "django.contrib.sessions." + DBSessionStore.__qualname__

    def __init__(self, *args, on_before_explicit_save=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_before_explicit_save = on_before_explicit_save
        self.save_calls = []

    def save(self, must_create=False):
        self.save_calls.append(must_create)
        if not must_create and self._on_before_explicit_save is not None:
            hook = self._on_before_explicit_save
            self._on_before_explicit_save = None  # fire exactly once
            hook()
        return super().save(must_create=must_create)


@pytest.mark.django_db
def test_concurrent_session_deletion_propagates_upstream_and_keeps_the_row_deleted():
    """Request B's login save detecting request A's delete propagates, never recreates.

    Request A (same cookie) logs out and deletes the shared server-side session row
    between request B's login key-write and B's explicit ``save``. B is on the
    retain-key path (same user, matching auth hash), so its ``save(must_create=
    False)`` hits the deleted row and the backend raises ``UpdateError``. The
    framework propagates that upstream interruption as a top-level GraphQL error
    with no success payload, compensates B's local actor to anonymous, and never
    recreates or overwrites the logged-out session.
    """
    create_users(1)
    schema = _login_logout_schema()
    user = get_user_model().objects.get(username="staff_1")

    # An existing durable authenticated session shared by both requests (cookie).
    seed_store = DBSessionStore()
    _establish_authenticated_django_session(user, seed_store)
    key = seed_store.session_key
    assert _session_row_exists(key)

    def _request_a_logs_out():
        # Request A deletes the shared row (its logout flush) mid-B-login.
        DBSessionStore(key).flush()

    b_store = _DeleteBeforeExplicitSaveStore(key, on_before_explicit_save=_request_a_logs_out)
    b_request = RequestFactory().post("/graphql/")
    b_request.session = b_store
    b_request.user = AnonymousUser()

    res = schema.execute_sync(
        _LOGIN_VAR_Q,
        variable_values={"u": "staff_1", "p": TEST_USER_PASSWORD},
        context_value=b_request,
    )

    assert res.errors is not None
    assert res.data is None or res.data.get("login") is None
    assert isinstance(res.errors[0].original_error, UpdateError)
    # B retained the key (no cycle), so the only explicit save was must_create=False.
    assert b_store.save_calls == [False]
    assert not b_request.user.is_authenticated  # compensation anonymized the actor
    # The logged-out session stays deleted; B never recreated it. The single
    # must_create=False save (no must_create=True cycle) proves B stayed on the
    # retain-key path and never minted a fresh session row to overwrite it with.
    assert not _session_row_exists(key)
