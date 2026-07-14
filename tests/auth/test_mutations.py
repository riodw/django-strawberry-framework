"""Package-internal tests for ``django_strawberry_framework/auth/mutations.py`` (spec-040).

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

import itertools

import pytest
import strawberry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import models as djmodels
from django.test import RequestFactory
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.auth import login_mutation, logout_mutation, register_mutation
from django_strawberry_framework.auth.mutations import (
    _auth_declarations,
    _declared_auth_surface,
    bind_auth_mutations,
    derive_register_fields,
    iter_auth_mutations,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations import inputs as mutation_inputs
from django_strawberry_framework.mutations.inputs import _materialized_names
from django_strawberry_framework.mutations.resolvers import _model_decode_step
from django_strawberry_framework.mutations.sets import _mutation_registry
from django_strawberry_framework.registry import (
    iter_subsystem_clears,
    registry,
)
from django_strawberry_framework.utils.querysets import SyncMisuseError

User = get_user_model()


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


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _session_request(user=None):
    """Build a real request with a working session (the auth transport contract)."""
    request = RequestFactory().post("/graphql/")
    SessionMiddleware(lambda _request: None).process_request(request)
    request.user = user if user is not None else AnonymousUser()
    return request


def _finalize_schema(mutation_type: type, *, query_type: type = _Query) -> strawberry.Schema:
    finalize_django_types()
    return strawberry.Schema(query=query_type, mutation=mutation_type)


def _login_logout_schema(**login_kwargs):
    """Declare UserT + a login/logout Mutation; return the finalized schema."""
    _declare_user_type()

    @strawberry.type
    class Mutation:
        login = login_mutation(**login_kwargs)
        logout = logout_mutation()

    return _finalize_schema(Mutation)


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
