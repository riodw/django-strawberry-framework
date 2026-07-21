"""Session-auth mutation factories + the phase-2.5 auth bind (spec-040).

The package's opt-in session-auth surface: ``login_mutation()`` /
``logout_mutation()`` (this module), ``register_mutation()`` (this module - a
narrow ``DjangoMutation`` rider, spec-040 Decision 6), and ``current_user()``
(``auth/queries.py``). Everything here is a thin layer over the frozen write
foundation - the declaration-ledger mechanics come from ``mutations.sets``,
payload construction from ``mutations.inputs``, authorization + the envelope
leaf ctors from ``mutations.resolvers``, and request resolution from
``utils.permissions`` (the spec-040 Helper-reuse obligations). The genuinely new
machinery is the session resolver pair (``django.contrib.auth.authenticate`` /
``login`` / ``logout`` behind the ``FieldError`` envelope), the register rider's
password-aware decode / write step pair, and ``bind_auth_mutations()`` - the
surface-keyed phase-2.5 bind ``types/finalizer.py`` runs BEFORE
``bind_mutations()`` (spec-040 Decision 9).

Lifecycle (Decision 9): the auth **declaration** ledger below is a
``make_declaration_registry`` instance cleared by ``TypeRegistry.clear()`` only
(an owner-registered callback without the ``before_bind`` phase flag, so the
finalizer cannot drain declarations before this module's bind reads them). The **emit** artifacts ride
the pre-bind seam: ``LoginPayload`` / ``LogoutPayload`` ride the existing
``mutations.inputs`` row (imported transitively here), and the ``current_user``
alias namespace rides ``auth/queries.py``'s own row. The ledger is ALSO the
holders' / rider's same-args cache and conflict state (the Revision-7 reload
finding): draining it drains the cache, so a post-``registry.clear()``
re-declaration with different ``permission_classes`` mints a fresh holder /
rider instead of tripping a stale conflict raise.
"""

from __future__ import annotations

import contextlib
import functools
from typing import Any

import strawberry
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from strawberry.utils.inspect import in_async_context

from ..exceptions import ConfigurationError
from ..mutations.fields import (
    DjangoMutationField,
    _lazy_ref,
    build_lazy_field_signature,
)
from ..mutations.inputs import (
    CREATE,
    INPUTS_MODULE_PATH,
    build_mutation_input,
    build_payload_type,
    editable_input_fields,
    materialize_mutation_input_class,
    mutation_input_shape,
    payload_object_slot,
)
from ..mutations.sets import (
    DjangoMutation,
    _validate_permission_classes,
    make_declaration_registry,
)
from ..mutations.sets import (
    register_mutation as record_mutation_declaration,
)
from ..registry import register_subsystem_clear, registry
from ..utils.permissions import request_from_info
from ..utils.querysets import run_in_one_sync_boundary
from . import sessions

# The one family label every auth surface resolves its request under (the
# spec-040 D1 reuse directive): a single module-level constant, never a per-field
# string literal, so the ``request_from_info`` resolution wording cannot drift
# between the four auth fields.
_AUTH_FAMILY_LABEL = "AuthMutation"

# The single undifferentiated login-failure message (the upstream borrow, spec-040
# Decision 5): deliberately NOT split into "unknown user" vs "wrong password" - an
# account-enumeration oracle - and byte-identical for both, pinned by the live
# enumeration-guard test.
_INCORRECT_CREDENTIALS_MESSAGE = "Incorrect username/password"

# The actionable WebSocket-login rejection (auth session-lifecycle hardening,
# Commit 3 / root cause 3): login rotates the session key, but an established
# WebSocket cannot return the replacement cookie, so a "success" would establish a
# server-side session the browser can never claim. The rejection fires BEFORE any
# authentication or session mutation. This is NOT part of the byte-compatible
# failed-login envelope (it is a transport-capability configuration error, a
# top-level GraphQL error), so its wording is free.
_WEBSOCKET_LOGIN_UNSUPPORTED = (
    "login_mutation() cannot establish a session over a WebSocket connection: an "
    "established WebSocket cannot return the rotated session cookie that login produces, "
    "so the browser could never reuse the session. Perform login over an HTTP request "
    "(Django HTTP or Channels HTTP) and connect the authenticated WebSocket afterwards."
)

# The actionable signed-cookie WebSocket-logout rejection (auth session-lifecycle
# hardening, Commit 4 / root cause 3): logout is supportable on a server-side
# session engine (deleting the record invalidates the old cookie without sending a
# new one), but a signed-cookie-engine WebSocket has NO server-side record to
# revoke and cannot delete or replace the browser cookie over an established
# socket, so a "success" would falsely claim durable invalidation. The rejection
# fires BEFORE any session mutation. Like the login rejection it is a
# transport-capability configuration error (a top-level GraphQL error), NOT part
# of the byte-compatible failed-login envelope, so its wording is free.
_WEBSOCKET_LOGOUT_UNSUPPORTED = (
    "logout_mutation() cannot truthfully invalidate a session over a signed-cookie "
    "WebSocket connection: the signed-cookie session engine keeps no server-side record "
    "to revoke, and an established WebSocket cannot delete or replace the browser cookie, "
    "so logout could not prove the session was invalidated. Use a server-side session "
    "engine for WebSocket logout, or perform logout over an HTTP request."
)

# The register rider's pinned public input name (spec-040 Decision 6): the
# consumer-facing SDL contract, pinned via the ``input_type_name`` /
# ``build_input`` name seams because the model-derived default would be the
# deterministic shape name (``UserEmailPasswordUsernameInput``). The PAYLOAD name
# has no seam - it derives from the rider's ``__name__`` (``Register`` ->
# ``RegisterPayload``) through the unchanged machinery.
_REGISTER_INPUT_NAME = "RegisterInput"

# The register exclusion seam's protected input attrs (spec-040 D6): ``password``
# is captured out of the model construction (never a constructed model attr) with
# its AR-H2 provided-marker preserved.
_REGISTER_EXCLUDED_INPUT_FIELDS = frozenset({"password"})

# Account-control fields Django's stock auth mixins place on user models. A
# custom user model may list ordinary identity/profile fields in
# ``REQUIRED_FIELDS``, but making one of these fields client-selectable on the
# package's public registration surface would turn a model declaration into a
# privilege or activation-control input.
_REGISTER_PROTECTED_FIELDS = frozenset(
    {
        "groups",
        "is_active",
        "is_staff",
        "is_superuser",
        "user_permissions",
    },
)

# surface key -> the consumer-facing factory name the bind errors cite (spec-040
# Decision 8: the three user-typed arms fail with the same actionable auth
# message, each naming the factory the consumer actually wrote).
_SURFACE_FACTORY_NAMES = {
    "login": "login_mutation()",
    "logout": "logout_mutation()",
    "register": "register_mutation()",
    "current_user": "current_user()",
}

# The auth DECLARATION ledger (spec-040 Decision 9 / D14): a
# ``make_declaration_registry`` instance - the same identity-deduped ``register``
# / post-finalize reject / ``clear`` mechanics the model / form flavors use, over
# its own disjoint store. Cleared by ``TypeRegistry.clear()`` ONLY (the hand row
# in ``registry.py``), never by the pre-bind reset - declarations must survive a
# recover-in-place re-finalize so ``bind_auth_mutations()`` can re-read them.
_auth_declaration_registry = make_declaration_registry(_AUTH_FAMILY_LABEL)
register_auth_mutation = _auth_declaration_registry.register
clear_auth_mutation_registry = _auth_declaration_registry.clear
iter_auth_mutations = _auth_declaration_registry.iter_
_auth_declarations = _auth_declaration_registry.store
register_subsystem_clear(clear_auth_mutation_registry, owner="auth.declarations")


class _AuthMutationMetaSnapshot:
    """The duck-typed ``_mutation_meta`` shape a fixed-field permission holder carries.

    ``DjangoMutation.check_permission`` reads only
    ``type(self)._mutation_meta.permission_classes`` (spec-040 Decision 5), so the
    holder's snapshot needs exactly the normalized ``permission_classes`` plus the
    pinned operation string - it is deliberately NOT a ``_ValidatedMutationMeta``
    (which would require ``model`` / ``operation`` constructor kwargs a model-less
    session field does not have).
    """

    __slots__ = ("operation", "permission_classes")

    def __init__(self, operation: str, permission_classes: list[Any]) -> None:
        self.operation = operation
        self.permission_classes = permission_classes


def _make_permission_holder(
    operation: str,
    holder_name: str,
    permission_classes: list[Any],
) -> type:
    """Synthesize the module-internal permission holder for one fixed auth field.

    The ONE holder-synthesis site the three fixed factories share (spec-040 D3 /
    P4): a tiny zero-arg-constructible class carrying the duck-typed shape
    ``authorize_or_raise`` requires - a ``_mutation_meta``-shaped snapshot (the
    normalized ``permission_classes`` + the pinned ``operation`` string), a
    ``_primary_type`` slot (set at bind for ``login`` / ``current_user``; left
    ``None`` for the model-less ``logout``, whose denial target then falls back to
    the holder ``__name__`` - which is why the logout holder is named ``Session``,
    so its denial string reads ``"Not authorized to logout Session."``), and
    ``DjangoMutation.check_permission`` bound directly, so the permission
    iteration, the ``GraphQLError`` denial, and the async-hook ``SyncMisuseError``
    guard are all reused **by call** (D2 / D4). A custom ``has_permission``
    receives the holder itself as its ``mutation`` positional - it carries no
    ``Meta.model`` / ``_resolve_model``, so gates must key on ``info`` /
    ``operation`` / ``data``, never on the mutation object (Decision 5's
    documented, not factory-guarded, constraint).
    """
    return type(
        holder_name,
        (),
        {
            "_mutation_meta": _AuthMutationMetaSnapshot(operation, permission_classes),
            "_auth_surface": operation,
            "_primary_type": None,
            "_payload_type_name": None,
            "check_permission": DjangoMutation.check_permission,
            "__doc__": (
                f"Module-internal permission carrier for the auth {operation!r} field "
                "(spec-040 Decision 5)."
            ),
        },
    )


def _declared_auth_surface(surface: str) -> type | None:
    """Return the ledger's declaration for ``surface``, or ``None``.

    The ledger IS the same-args cache and the conflict state (spec-040 Decision 9
    / Revision 7): the cached holders / rider are looked up through the
    declaration records, never a separate module dict a ``registry.clear()``
    would miss, so draining the ledger drains the cache.
    """
    for declaration_cls in iter_auth_mutations():
        if getattr(declaration_cls, "_auth_surface", None) == surface:
            return declaration_cls
    return None


def _reject_conflicting_permission_classes(
    surface: str,
    declared_cls: type,
    permission_classes: list[Any],
) -> None:
    """Raise unless a repeat declaration's ``permission_classes`` match the cached one.

    The one-declaration-per-process rule (spec-040 Decision 6 / Edge cases): the
    fixed payload names (``LoginPayload`` / ``RegisterPayload`` / ...) cannot
    serve two distinct permission-specialized classes, so a second same-surface
    call with a DIFFERENT ``permission_classes`` raises loudly instead of
    colliding late at materialize. The conflict / cache key is the
    schema-affecting declaration args ONLY - today exactly the normalized
    ``permission_classes``; ``description`` / ``deprecation_reason`` /
    ``directives`` are per-field presentation kwargs and never enter the key.
    """
    declared = list(declared_cls._mutation_meta.permission_classes)
    if declared != list(permission_classes):
        factory = _SURFACE_FACTORY_NAMES[surface]
        raise ConfigurationError(
            f"auth {factory} is already declared in this process with permission_classes="
            f"{[cls.__name__ for cls in declared]!r}; a second call with a different "
            f"permission_classes ({[cls.__name__ for cls in permission_classes]!r}) cannot mint "
            "a second fixed-name auth payload. Declare each auth surface once per process with "
            "one permission set (registry.clear() resets the declaration).",
        )


def _declare_auth_surface(
    surface: str,
    label: str,
    permission_classes: Any,
    synthesize: Any,
) -> type:
    """Resolve one auth surface's declaration class (cached, conflict-checked, or fresh).

    The ONE declaration path all four factories route through: normalize
    ``permission_classes`` via the standard ``_validate_permission_classes`` with
    the explicit empty-list default (the AllowAny semantics - the documented
    inversion of the write family's deny-by-default; no ``AllowAny`` class exists,
    spec-040 Decision 5), then either return the ledger-cached class (a
    same-``permission_classes`` repeat call), raise on a conflicting repeat, or
    mint a fresh class via ``synthesize(normalized)`` (a permission holder for the
    fixed fields; the ``Register`` rider for ``register_mutation``). Ledger
    RECORDING stays at the call sites - the fixed path appends to the auth ledger
    only, while ``register_mutation`` appends to BOTH ledgers - so the every-call
    re-record semantics (the reload contract) are explicit where they differ.
    """
    normalized = _validate_permission_classes(label, permission_classes, unset_default=())
    declared_cls = _declared_auth_surface(surface)
    if declared_cls is not None:
        _reject_conflicting_permission_classes(surface, declared_cls, normalized)
        return declared_cls
    return synthesize(normalized)


def _declare_fixed_auth_surface(surface: str, holder_name: str, permission_classes: Any) -> type:
    """Record (or re-record) one fixed auth surface; return its permission holder.

    The shared fixed-field declaration path ``login_mutation`` /
    ``logout_mutation`` / ``current_user`` all route through:
    ``_declare_auth_surface`` resolves the holder (cached / conflict-raise /
    fresh-minted via ``_make_permission_holder``), then the holder is
    re-registered so a drained ledger re-appends (the reload contract). The
    ``register_auth_mutation`` call also enforces the standing
    declare-after-finalize ``ConfigurationError``.
    """
    holder_cls = _declare_auth_surface(
        surface,
        holder_name,
        permission_classes,
        lambda normalized: _make_permission_holder(surface, holder_name, normalized),
    )
    register_auth_mutation(holder_cls)
    return holder_cls


def _sync_bridged_async_body(sync_body: Any) -> Any:
    """Build the interim async resolver body that bridges to ``sync_body`` (spec-040 D17).

    The auth session-lifecycle hardening plan (Commit 2) splits ``_make_auth_field``
    into a real sync resolver body and a real *async* resolver body so later stages
    can inject native per-transport async work. This slice is the SEAM only, so the
    async body is (for now) a genuine ``async def`` coroutine function that bridges
    to ``sync_body`` through the ONE shared ``sync_to_async(thread_sensitive=True)``
    worker - request resolution, the permission gate (whose ``instance=request.user``
    argument forces the ``SimpleLazyObject`` as it is computed, a sync ORM touch),
    and the session work all run inside that single boundary. The ``SyncMisuseError``
    discipline is unaffected: the worker is itself a sync context, so an ``async def
    has_permission`` is still rejected there, never silently allowed. Commits 3/4
    replace this bridge, per surface, with native Django/Channels async bodies
    without touching the dispatch seam below.
    """

    async def _async_body(info: Any, **kwargs: Any) -> Any:
        return await run_in_one_sync_boundary(sync_body, info, **kwargs)

    return _async_body


def _make_auth_field(
    *,
    sync_body: Any,
    async_body: Any,
    arguments: list[tuple[str, Any]],
    return_annotation: Any,
    description: str | None,
    deprecation_reason: str | None,
    directives: Any,
) -> Any:
    """Build one fixed auth field around split sync / async gate-then-session-work bodies.

    The ONE auth field-construction helper the three fixed factories share
    (spec-040 D12 / P1 / P2; auth session-lifecycle hardening Commit 2): the
    dispatcher resolves sync-vs-async per call via ``in_async_context()`` (the
    ``DjangoMutationField`` runtime dispatch). The sync path calls ``sync_body``
    directly; the async path calls ``async_body`` - a real coroutine function whose
    returned coroutine Strawberry awaits - so no native async work is hidden behind
    a nested ``async_to_sync`` inside a sync body. ``sync_body`` and ``async_body``
    are the per-surface injection points later stages specialize per transport; the
    dispatch seam itself does not change. The injected ``__signature__`` /
    ``__annotations__`` (the keyword-only GraphQL args + the ``strawberry.lazy``
    return forward-ref, unresolved at class-body time) ride the promoted
    ``mutations/fields.py`` machinery - ``build_lazy_field_signature`` over
    ``_lazy_ref``-built refs - never a re-spelled copy. ``arguments`` is the ordered
    ``(name, annotation)`` list of keyword-only GraphQL args (empty for ``logout`` /
    ``me``).
    """

    def _resolve(root: Any, info: Any, **kwargs: Any) -> Any:  # noqa: ARG001
        if in_async_context():
            return async_body(info, **kwargs)
        return sync_body(info, **kwargs)

    signature, annotations = build_lazy_field_signature(arguments, return_annotation)
    _resolve.__signature__ = signature
    _resolve.__annotations__ = annotations
    return strawberry.field(
        resolver=_resolve,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )


def _authenticated_actor_or_none(request: Any) -> Any:
    """Return the request's authenticated actor, or ``None`` when anonymous.

    The ONE anonymity definition the session-auth surfaces share (spec-040
    Decision 5 / Decision 7): a request with no ``user`` attribute
    (SessionMiddleware without AuthenticationMiddleware, or a Channels adapter
    whose scope carries no auth-middleware user) and a request whose ``user`` is
    not authenticated both classify as anonymous. ``logout``'s ``ok`` flag and
    ``current_user``'s nullable return both derive from this result
    (``actor is not None`` / the actor itself) so the classification cannot drift
    between the two fields.
    """
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return user
    return None


def _failed_login_payload(payload_cls: type, slot: str) -> Any:
    """Build the ONE undifferentiated failed-login envelope (spec-040 Decision 5).

    ``node``/``result`` is ``None`` and ``errors`` carries a single non-field-keyed
    entry - the ``field_error("", ...)`` empty-path leaf owns the ``"__all__"``
    sentinel (the D8 reuse directive). No error code, deliberately: the public
    failed-login contract is ``field: "__all__"`` + the one message ONLY, so both
    wrong-password / unknown-user / inactive-under-``ModelBackend`` / unstorable
    credential collapse to a byte-identical payload (the enumeration guard).
    """
    from ..mutations import resolvers

    error = resolvers.field_error("", _INCORRECT_CREDENTIALS_MESSAGE)
    return resolvers.build_payload(payload_cls, slot, None, [error])


def _transport_prologue(
    info: Any,
    *,
    supported: Any,
    unsupported_message: str,
) -> tuple[Any, sessions.Transport, Any]:
    """Resolve + classify the request, enforce transport capability, require a session.

    The ONE shared transport prologue login and logout both open with (auth
    session-lifecycle hardening): classify the transport, reject an unsupported
    transport BEFORE any authentication or session mutation, then run the
    missing-session-middleware guard. ``supported`` is the per-surface capability
    predicate (``sessions.login_supported`` / ``sessions.logout_supported``) and
    ``unsupported_message`` its actionable rejection. Step ordering is fixed:
    classify -> capability -> require_session. Returns ``(request, transport,
    session)``; logout ignores the returned session (its durability is the native
    flush, not a resolver-side save) but still runs ``require_session`` for its
    rejection side effect.
    """
    request = request_from_info(info, family_label=_AUTH_FAMILY_LABEL)
    transport = sessions.classify_transport(request)
    if not supported(transport):
        raise ConfigurationError(unsupported_message)
    session = sessions.require_session(request, transport)
    return request, transport, session


def _login_result_payload(payload_cls: type, slot: str, user: Any) -> Any:
    """Build the failed-login envelope when ``user`` is ``None``, else the success payload.

    The shared two-line payload construction both login bodies (sync + async) open
    their post-authenticate step with (auth session-lifecycle hardening). Building
    the failed envelope is a pure construction with no session mutation, so callers
    build the payload here and THEN early-return on the failed case, preserving both
    the failed-login early return and the payload-before-mutation ordering.
    """
    from ..mutations import resolvers

    if user is None:
        return _failed_login_payload(payload_cls, slot)
    return resolvers.build_payload(payload_cls, slot, user, [])


def _login_authenticate(
    holder_cls: type,
    info: Any,
    username: str,
    password: str,
) -> tuple[Any, sessions.Transport, Any, type, str, Any]:
    """The all-sync login prologue: classify, capability, gate, preflight, authenticate.

    Runs steps 1-5 of the login state machine (auth session-lifecycle hardening,
    Commit 3) with NO session mutation:

    1. resolve + classify the transport (``sessions.classify_transport``);
    2. capability check - a WebSocket login is rejected here, BEFORE authentication
       or any session mutation (``sessions.login_supported``); a missing session
       middleware is the actionable ``"session"`` configuration error
       (``sessions.require_session``);
    3. the permission gate (``data`` carries only the attempted ``username``, NEVER
       the password, so an account-scoped rate-limit gate can key on it; a denial is
       the top-level ``GraphQLError`` and credentials are never checked);
    4. the shared storability preflight - a lone-surrogate credential is not UTF-8
       encodable and would crash ``authenticate`` into a raw ``UnicodeEncodeError``
       (the DB ``USERNAME_FIELD`` lookup / the password hasher's ``.encode()``), so
       it short-circuits to the SAME undifferentiated envelope (``user`` ``None``),
       reusing the ONE write-side ``unencodable_text_error`` primitive;
    5. exactly ONE ``authenticate(request, username=, password=)`` call - no local
       user-model query (the actor-not-lookup rule, D-N1).

    Returns ``(request, transport, session, payload_cls, slot, user)``; ``user`` is
    ``None`` for both the unstorable and the failed-authentication cases (the caller
    maps either to ``_failed_login_payload`` without touching the session). This is
    sync-only so BOTH the native sync body and the native async body (inside its one
    ``sync_to_async`` boundary) reuse it without duplicating the state machine.
    """
    from ..mutations import resolvers
    from ..utils.write_values import unencodable_text_error

    request, transport, session = _transport_prologue(
        info,
        supported=sessions.login_supported,
        unsupported_message=_WEBSOCKET_LOGIN_UNSUPPORTED,
    )
    resolvers.authorize_or_raise(holder_cls, info, "login", {"username": username}, instance=None)
    payload_cls = resolvers.payload_cls_for(holder_cls)
    slot = payload_object_slot(holder_cls._primary_type)
    unstorable = (
        unencodable_text_error("username", username) is not None
        or unencodable_text_error("password", password) is not None
    )
    user = None if unstorable else auth.authenticate(request, username=username, password=password)
    return request, transport, session, payload_cls, slot, user


def _django_http_login_establish(request: Any, user: Any) -> None:
    """Establish + durably persist the Django HTTP session; compensate fail-closed.

    Django's native ``login`` performs session rotation (``cycle_key`` for
    anonymous->auth, ``flush`` for a different / hash-mismatched user), selects the
    backend from ``user.backend`` (never a framework second lookup), writes the auth
    keys, assigns ``request.user``, rotates CSRF, and fires ``user_logged_in`` (which
    updates ``user.last_login``). The explicit ``request.session.save()`` then makes
    a store failure a GraphQL execution error BEFORE any success payload; the
    ``modified`` flag is deliberately left set so ``SessionMiddleware`` still saves
    and emits the rotated cookie (clearing it would suppress the cookie transition
    that makes the durable session usable).

    On ANY failure after partial mutation (backend-selection ``ValueError``, a
    ``cycle_key``/``flush``/``save`` store outage, or a raising ``user_logged_in``
    receiver) the local actor is made anonymous and the partially established
    session is flushed - clearing the in-memory auth keys AND deleting the durable
    rotated/empty row ``cycle_key``/``flush`` already wrote. If cleanup also raises,
    the ORIGINAL failure is re-raised with the cleanup error chained via
    ``__context__`` (PEP 3134), never a false clean-state claim, and never a success
    payload. This path holds no asyncio lock - the lock is Channels-scope-only.
    """
    try:
        auth.login(request, user)
        request.session.save()
    except BaseException as primary:  # incl. asyncio.CancelledError: compensate + re-raise
        try:
            request.user = AnonymousUser()
            request.session.flush()
        except Exception:
            raise primary  # noqa: B904 - cleanup failure chains via __context__ (PEP 3134)
        raise


async def _channels_http_login_establish(request: Any, session: Any, user: Any) -> None:
    """Establish + durably persist the Channels HTTP session; compensate fail-closed.

    The Channels twin of ``_django_http_login_establish``, awaited natively (never a
    nested ``async_to_sync`` on the router's async consumer). ``channels.auth.login``
    (a ``database_sync_to_async`` callable) performs the same rotation, selects the
    backend from ``user.backend``, writes the auth keys, sets ``scope["user"]``, and
    fires ``user_logged_in`` (``request=None``, but ``update_last_login`` keys on
    ``user`` so ``last_login`` still updates). Channels' ``login`` does NOT persist
    the written keys, so the explicit ``await session.asave()`` is the durability
    step the transport contract requires before success; Channels' response
    middleware then sends the cookie.

    The whole critical section runs under the per-scope ``asyncio.Lock`` acquired
    ONCE here (``scope_session_lock`` is non-reentrant, so compensation runs inside
    the already-held lock and calls no helper that re-acquires it). Compensation
    makes the scope actor anonymous and flushes the session (clearing the in-memory
    auth keys AND deleting the durable rotated/empty row); a cleanup failure chains
    the original failure via ``__context__`` (PEP 3134).
    """
    from channels.auth import login as channels_login

    async with sessions.scope_session_lock(request):
        try:
            await channels_login(request.scope, user)
            await session.asave()
        except BaseException as primary:  # incl. asyncio.CancelledError: compensate + re-raise
            try:
                request.scope["user"] = AnonymousUser()
                await session.aflush()
            except Exception:
                raise primary  # noqa: B904 - cleanup chains via __context__ (PEP 3134)
            raise


def _login_resolve_body(
    holder_cls: type,
    info: Any,
    *,
    username: str,
    password: str,
) -> Any:
    """The native SYNC login body: prologue, then the transport critical section.

    Handles Django HTTP under synchronous execution directly, and a directly-invoked
    Strawberry ``SyncGraphQLHTTPConsumer`` (a classified Channels HTTP scope) through
    a SINGLE ``async_to_sync`` bridge at the private transport boundary (the plan's
    one permitted sync->async hop; the package router's async consumer instead awaits
    the native async body). The success payload is constructed BEFORE the session is
    mutated (step 6) so a payload-construction failure cannot create a session the
    client never sees, and it holds the authenticated user OBJECT (not a scalar
    snapshot) so nested GraphQL fields resolve after login and observe the
    signal-updated ``last_login``.
    """
    request, transport, session, payload_cls, slot, user = _login_authenticate(
        holder_cls,
        info,
        username,
        password,
    )
    payload = _login_result_payload(payload_cls, slot, user)
    if user is None:
        return payload
    if transport is sessions.Transport.CHANNELS_HTTP:
        from asgiref.sync import async_to_sync

        async_to_sync(_channels_http_login_establish)(request, session, user)
    else:
        _django_http_login_establish(request, user)
    return payload


async def _login_resolve_body_async(
    holder_cls: type,
    info: Any,
    *,
    username: str,
    password: str,
) -> Any:
    """The native ASYNC login body: bridge Django HTTP, await Channels HTTP natively.

    A Django ``HttpRequest`` under async execution stays inside the existing
    thread-sensitive sync boundary (``run_in_one_sync_boundary`` around the sync body
    exactly once - the same bridge the other auth fields use). A classified Channels
    HTTP scope runs the all-sync prologue (gate + preflight + ``authenticate``) inside
    ONE sync boundary, constructs the success payload before mutation, then awaits the
    native ``channels.auth.login`` + ``session.asave()`` establishment - no nested
    ``async_to_sync``. The transport classification runs on the event loop (pure, no
    ORM), so it never trips ``SynchronousOnlyOperation``.
    """
    request = request_from_info(info, family_label=_AUTH_FAMILY_LABEL)
    if sessions.classify_transport(request) is not sessions.Transport.CHANNELS_HTTP:
        return await run_in_one_sync_boundary(
            _login_resolve_body,
            holder_cls,
            info,
            username=username,
            password=password,
        )
    request, _transport, session, payload_cls, slot, user = await run_in_one_sync_boundary(
        _login_authenticate,
        holder_cls,
        info,
        username,
        password,
    )
    payload = _login_result_payload(payload_cls, slot, user)
    if user is None:
        return payload
    await _channels_http_login_establish(request, session, user)
    return payload


def _logout_prologue(holder_cls: type, info: Any) -> tuple[Any, sessions.Transport, type]:
    """The all-sync logout prologue: classify, capability, missing-session, gate, payload class.

    Runs steps 1-3 of the logout state machine (auth session-lifecycle hardening,
    Commit 4) with NO session mutation:

    1. resolve + classify the transport (``sessions.classify_transport``), then the
       capability check - a signed-cookie-engine WebSocket logout is rejected here,
       BEFORE any teardown (``sessions.logout_supported``); a missing session
       middleware is the actionable ``"session"`` configuration error
       (``sessions.require_session``) rather than a downstream ``AttributeError``;
    2. the permission gate (the model-less denial target reads the holder
       ``__name__`` - the pinned ``"Not authorized to logout Session."`` string);
    3. resolve the ``{ ok, errors }`` payload class without mutating the session.

    Returns ``(request, transport, payload_cls)``. This is sync-only so BOTH the
    native sync body and the native async body (inside its one ``sync_to_async``
    boundary) reuse it without duplicating the state machine. ``require_session`` is
    called for its rejection side effect; its return is unused because logout's
    durability is the native flush, not a resolver-side save.
    """
    from ..mutations import resolvers

    request, transport, _session = _transport_prologue(
        info,
        supported=sessions.logout_supported,
        unsupported_message=_WEBSOCKET_LOGOUT_UNSUPPORTED,
    )
    resolvers.authorize_or_raise(holder_cls, info, "logout", None, instance=None)
    payload_cls = resolvers.payload_cls_for(holder_cls)
    return request, transport, payload_cls


def _logout_observation(request: Any, payload_cls: type) -> Any:
    """Capture the pre-teardown ``ok`` observation and build the logout payload.

    The shared pair both logout teardowns open their critical section with (auth
    session-lifecycle hardening): ``ok`` is whether an authenticated actor existed
    (the ONE anonymity definition shared with ``current_user``) and the
    ``{ ok, errors }`` payload is constructed BEFORE any session mutation, so ``ok``
    describes the state being transitioned and payload construction cannot fail after
    teardown. The Channels caller invokes this inside the held per-scope lock, the
    same point the observation is captured today.
    """
    ok = _authenticated_actor_or_none(request) is not None
    return payload_cls(ok=ok, errors=[])


def _django_http_logout(request: Any, payload_cls: type) -> Any:
    """Capture the actor, build the payload, then run Django's native logout; fail closed.

    The Django HTTP teardown (auth session-lifecycle hardening, Commit 4). The
    ``ok`` observation is captured BEFORE teardown via ``_authenticated_actor_or_none``
    (the ONE anonymity definition shared with ``current_user``) and the payload is
    constructed before mutation, so ``ok`` describes the state actually being
    transitioned and payload construction cannot fail after teardown. Django's native
    ``logout`` fires ``user_logged_out``, then ``request.session.flush()`` (which
    ``clear()`` + ``delete()`` - the durable invalidation, no resolver-side save
    needed), then assigns ``request.user = AnonymousUser()``. Teardown runs
    unconditionally, including for an anonymous request carrying residual session
    data. On ANY failure (a raising ``user_logged_out`` receiver before flush, or a
    store outage during ``flush``/``delete``) the local actor is made anonymous where
    possible and the error propagates - never a false ``{ok: true}``. This path holds
    no asyncio lock; the scope lock is Channels-scope-only.
    """
    payload = _logout_observation(request, payload_cls)
    try:
        auth.logout(request)
    except BaseException:  # incl. asyncio.CancelledError: anonymize where possible + re-raise
        with contextlib.suppress(Exception):
            request.user = AnonymousUser()
        raise
    return payload


async def _channels_logout(request: Any, payload_cls: type) -> Any:
    """The Channels twin of ``_django_http_logout``, awaited natively under the scope lock.

    ``channels.auth.logout`` (a ``database_sync_to_async`` callable) fires
    ``user_logged_out``, then ``session.flush()`` (the durable invalidation: on a
    server-side engine the record is deleted so the old cookie can never be
    reclaimed, and on Channels HTTP the response middleware sees the emptied session
    and deletes/replaces the browser cookie), then sets
    ``scope["user"] = AnonymousUser()``. Channels' flush is itself durable, so no
    explicit ``asave()`` is added here (that would double-flush); logout's durability
    requirement is complete via the native teardown, unlike login's key-write which
    needs the explicit save.

    The whole critical section runs under the per-scope ``asyncio.Lock`` acquired
    ONCE here (``scope_session_lock`` is non-reentrant): the under-lock actor capture
    (the ``ok`` observation), payload construction, native teardown, and failure
    handling are atomic against any other operation multiplexed on the same Channels
    connection. On failure the scope actor is made anonymous where possible and the
    error propagates - never a false ``{ok: true}`` and never a claimed clean durable
    state the teardown did not achieve.
    """
    from channels.auth import logout as channels_logout

    async with sessions.scope_session_lock(request):
        payload = _logout_observation(request, payload_cls)
        try:
            await channels_logout(request.scope)
        except BaseException:  # incl. asyncio.CancelledError: anonymize where possible + re-raise
            with contextlib.suppress(Exception):
                request.scope["user"] = AnonymousUser()
            raise
        return payload


def _logout_resolve_body(holder_cls: type, info: Any) -> Any:
    """The native SYNC logout body: prologue, then the transport critical section.

    Handles Django HTTP under synchronous execution directly, and a directly-invoked
    Strawberry ``SyncGraphQLHTTPConsumer`` (a classified Channels HTTP scope) through
    a SINGLE ``async_to_sync`` bridge at the private transport boundary (the plan's
    one permitted sync->async hop; the package router's async consumer instead awaits
    the native async body). ``ok`` retains the shipped meaning: it is ``true`` only
    when an authenticated actor existed under the lock before teardown, and an
    already-anonymous logout returns ``{ok: false, errors: []}`` after still flushing
    any residual session data (idempotent teardown with an observational result). A
    Channels WebSocket cannot reach the sync body (the router's WS consumer is async),
    but is routed through the same bridge for completeness.
    """
    request, transport, payload_cls = _logout_prologue(holder_cls, info)
    if transport is sessions.Transport.DJANGO_HTTP:
        return _django_http_logout(request, payload_cls)
    from asgiref.sync import async_to_sync

    return async_to_sync(_channels_logout)(request, payload_cls)


async def _logout_resolve_body_async(holder_cls: type, info: Any) -> Any:
    """The native ASYNC logout body: bridge Django HTTP, await Channels natively.

    A Django ``HttpRequest`` under async execution stays inside the existing
    thread-sensitive sync boundary (``run_in_one_sync_boundary`` around the sync body
    exactly once - the same bridge the other auth fields use). A classified Channels
    scope (HTTP, or a server-side-engine WebSocket) runs the all-sync prologue (gate +
    capability + payload class) inside ONE sync boundary, then awaits the native
    ``channels.auth.logout`` teardown - no nested ``async_to_sync``. The transport
    classification runs on the event loop (pure, no ORM), so it never trips
    ``SynchronousOnlyOperation``.
    """
    request = request_from_info(info, family_label=_AUTH_FAMILY_LABEL)
    if sessions.classify_transport(request) is sessions.Transport.DJANGO_HTTP:
        return await run_in_one_sync_boundary(_logout_resolve_body, holder_cls, info)
    request, _transport, payload_cls = await run_in_one_sync_boundary(
        _logout_prologue,
        holder_cls,
        info,
    )
    return await _channels_logout(request, payload_cls)


def login_mutation(
    *,
    permission_classes: Any = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Any = (),
) -> Any:
    """Return the ``login(username:, password:)`` session mutation field (Decision 5).

    Two flat non-null ``String`` arguments (the ``username`` kwarg maps onto the
    user model's ``USERNAME_FIELD`` inside ``ModelBackend``, so an email-login
    custom user model works unchanged), resolving to the bind-materialized
    ``LoginPayload`` (the uniform object slot typed as the consumer's primary
    user ``DjangoType`` + the frozen ``errors`` envelope). ``permission_classes``
    defaults to the explicit empty list (allow-any - the documented auth
    inversion of deny-by-default).
    """
    holder_cls = _declare_fixed_auth_surface("login", "Login", permission_classes)
    return _make_auth_field(
        sync_body=functools.partial(_login_resolve_body, holder_cls),
        async_body=functools.partial(_login_resolve_body_async, holder_cls),
        arguments=[("username", str), ("password", str)],
        return_annotation=_lazy_ref("LoginPayload", INPUTS_MODULE_PATH),
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )


def logout_mutation(
    *,
    permission_classes: Any = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Any = (),
) -> Any:
    """Return the argument-less ``logout`` session mutation field (Decision 5).

    Resolves to the bind-materialized model-less ``LogoutPayload`` (the pinned
    ``{ ok: Boolean!, errors: [FieldError!]! }`` shape the plain form froze).
    ``ok`` is whether an authenticated session existed before the (idempotent)
    teardown. A logout-only schema needs NO registered user type - its payload
    references no user type and the surface-keyed bind never resolves one
    (Decision 8's structural exemption).
    """
    holder_cls = _declare_fixed_auth_surface("logout", "Session", permission_classes)
    return _make_auth_field(
        sync_body=functools.partial(_logout_resolve_body, holder_cls),
        async_body=functools.partial(_logout_resolve_body_async, holder_cls),
        arguments=[],
        return_annotation=_lazy_ref("LogoutPayload", INPUTS_MODULE_PATH),
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )


def derive_register_fields(user_model: type) -> tuple[str, ...]:
    """Return the register input's narrowed field tuple for ``user_model`` (Decision 6).

    The exact rule: ``USERNAME_FIELD`` first, then each distinct
    ``REQUIRED_FIELDS`` entry in declaration order, then ``password`` exactly
    once, deduplicated (an entry repeating ``USERNAME_FIELD`` or ``password``
    appears once). Takes the model as an argument - never reading
    ``get_user_model()`` inline - so both the default and a
    custom-``USERNAME_FIELD`` / custom-``REQUIRED_FIELDS`` model are directly
    testable with a test-scoped model (no ``AUTH_USER_MODEL`` swap). Unknown /
    non-editable / reverse names are rejected by DELEGATING to the standard
    ``editable_input_fields`` validation (which already raises a
    ``ConfigurationError`` naming field + model), never a re-implemented check.
    Known account-control fields (``is_active`` / ``is_staff`` /
    ``is_superuser`` / ``groups`` / ``user_permissions``) are rejected if a
    custom model places them in ``USERNAME_FIELD`` or ``REQUIRED_FIELDS``. This
    keeps privilege and activation state server-owned instead of silently
    turning an unusual user-model declaration into public registration input.
    """
    names = [user_model.USERNAME_FIELD, *user_model.REQUIRED_FIELDS, "password"]
    deduped = tuple(dict.fromkeys(names))
    protected = sorted(_REGISTER_PROTECTED_FIELDS.intersection(deduped))
    if protected:
        raise ConfigurationError(
            f"register_mutation() cannot auto-expose protected user field(s) {protected!r} "
            f"derived from {user_model.__name__}.USERNAME_FIELD / REQUIRED_FIELDS; remove "
            "those fields from the automatic registration surface and initialize account "
            "privileges and activation state in server-owned registration logic.",
        )
    # Delegate unknown / non-editable / reverse-name rejection to the standard
    # narrowing validation (single-sited message naming field + model).
    editable_input_fields(user_model, fields=deduped)
    return deduped


def _register_decode_step(
    model: type,
    data: Any,
    info: Any,
    instance: Any,
) -> Any:
    """The register ``decode_step``: the shared model decode + the password capture (D6).

    Rides ``_model_decode_step`` with the ``excluded_input_fields`` seam - the ONE
    shared UNSET-strip walk, never a fork - so ``password`` is captured out of the
    constructed model attrs (the raw value never touches
    ``model(**scalar_and_fk_attrs)``) while the AR-H2 exclude calculation still
    counts it as provided. Returns the extended decoded tuple
    ``(user, m2m_assignments, exclude, raw_password)`` - the raw password travels
    as explicit decoded state, never an implicit closure. ``password`` is a
    required input field (``AbstractBaseUser.password`` has no default / blank),
    so a reached decode always captured it.
    """
    from ..mutations.resolvers import _model_decode_step

    decoded = _model_decode_step(
        model,
        data,
        info,
        instance=instance,
        excluded_input_fields=_REGISTER_EXCLUDED_INPUT_FIELDS,
    )
    if isinstance(decoded, list):
        return decoded
    user, m2m_assignments, exclude, excluded_values = decoded
    return user, m2m_assignments, exclude, excluded_values["password"]


def _register_write_step(instance: Any, decoded: tuple[Any, ...]) -> Any:
    """The register ``write_step``: validate + hash the password, then the shared tail (D7).

    ``validate_password(raw_password, user)`` runs with the constructed (unsaved)
    instance so ``UserAttributeSimilarityValidator`` compares against the
    submitted username/email (the deliberate improvement over upstream's
    user-less call). A failure is keyed to ``password`` DIRECTLY at the call site
    (the D-N2 deliberate non-reuse: ``validate_password`` raises a list-style
    ``ValidationError`` with no ``error_dict``, and the generic
    ``validation_error_to_field_errors`` mapper would key it to the ``"__all__"``
    sentinel, not ``password``). Success hashes via ``set_password`` BEFORE
    ``full_clean()`` (the ``password`` column validates against the hash, never
    the raw input), then delegates ``full_clean`` -> ``save`` (race
    ``IntegrityError`` -> envelope) -> M2M to the shared model write tail -
    ``validate_password`` + ``set_password`` are the ONLY auth-specific steps.
    """
    from ..mutations import resolvers
    from ..utils.write_values import unencodable_text_error

    user, m2m_assignments, exclude, raw_password = decoded
    # ``password`` rides the D6 exclusion seam, so it bypasses the shared decode's
    # scalar storability preflight (``decode_scalar_leaf``) that every other input
    # scalar - including this register's own ``username`` - runs through. A
    # lone-surrogate password passes ``validate_password`` (none of its validators
    # encode the text) and then crashes ``set_password``'s hasher ``.encode()`` with a
    # raw ``UnicodeEncodeError``. Preflight it here via the SAME shared primitive the
    # model decode uses, so an unstorable password is the field-keyed ``password``
    # envelope (byte-identical to how the shared decode already rejects a surrogate
    # ``username``), never a top-level GraphQL error.
    text_error = unencodable_text_error("password", raw_password)
    if text_error is not None:
        return [text_error]
    try:
        validate_password(raw_password, user)
    except ValidationError as exc:
        codes = [leaf.code for leaf in exc.error_list if leaf.code]
        return [resolvers.field_error("password", exc.messages, codes=codes)]
    user.set_password(raw_password)
    return resolvers._model_write_step(instance, (user, m2m_assignments, exclude))


def _run_register_pipeline_sync(mutation_cls: type, info: Any, data: Any) -> Any:
    """Run the register create through the shared write skeleton (spec-040 Decision 6).

    Rides ``run_write_pipeline_sync`` unchanged - the ``transaction.atomic()``
    boundary, the authorize-before-decode ordering, the envelope short-circuits
    with rollback, and the closing by-pk-without-visibility ``refetch_optimized``
    (the ``036`` own-write exception: a staff-only ``UserType.get_queryset`` must
    not hide the account it just created) - supplying only the password-aware
    decode / write step pair. Structurally a fourth decode/write STEP PAIR, not a
    fourth plumbing kit.
    """
    from ..mutations.resolvers import run_write_pipeline_sync

    model = mutation_cls._mutation_meta.model
    return run_write_pipeline_sync(
        mutation_cls,
        info,
        data,
        strawberry.UNSET,
        decode_step=lambda instance: _register_decode_step(model, data, info, instance),
        write_step=_register_write_step,
    )


def _synthesize_register_rider(permission_classes: list[Any]) -> type:
    """Synthesize the concrete ``Register`` rider class (spec-040 Decision 6).

    A package-declared ``DjangoMutation`` subclass whose ``__name__`` is pinned to
    ``Register`` so the UNCHANGED machinery emits ``RegisterPayload`` (the payload
    name derives only from ``mutation_cls.__name__``; there is no payload-name
    seam, and ``DjangoRegisterMutation`` stays reserved for a possible
    consumer-facing base follow-on). Created lazily on first factory call - never
    at module import - because creating it records a mutation declaration, and a
    consumer importing ``auth`` only for ``login_mutation`` must not get a phantom
    user input/payload materialized at bind. The class-body declaration runs the
    standard metaclass validation + mutation-ledger registration (including the
    declare-after-finalize reject).
    """
    user_model = get_user_model()
    register_fields = derive_register_fields(user_model)
    rider_permission_classes = list(permission_classes)

    class Register(DjangoMutation):
        """The synthesized register rider: a narrow ``create`` over ``get_user_model()``."""

        _auth_surface = "register"

        class Meta:
            model = user_model
            operation = "create"
            fields = register_fields
            permission_classes = rider_permission_classes

        @classmethod
        def input_type_name(cls, meta: Any) -> str:
            """Pin the generated input's public name to ``RegisterInput`` (the name seam)."""
            del meta  # the register input name is fixed, not shape-derived.
            return _REGISTER_INPUT_NAME

        @classmethod
        def build_input(cls, meta: Any, primary_type: type) -> type:
            """Build the narrowed model-column input under the pinned ``RegisterInput`` name.

            The standard generator unchanged (``mutation_input_shape`` +
            ``build_mutation_input`` over the ``Meta.fields`` narrowing - ``email``
            optional per ``input_field_required``), with only the shape descriptor's
            ``type_name`` re-pinned so the class and its SDL name read
            ``RegisterInput`` instead of the deterministic shape-derived name.
            Materialized onto the standard ``mutations.inputs`` emit ledger so the
            AR-M6 distinct-shape collision raise still guards a consumer's own
            ``RegisterInput``.
            """
            shape = mutation_input_shape(meta.model, CREATE, fields=meta.fields)
            pinned = shape._replace(type_name=_REGISTER_INPUT_NAME)
            input_cls = build_mutation_input(
                meta.model,
                operation_kind=CREATE,
                primary_type=primary_type,
                fields=meta.fields,
                shape=pinned,
            )
            materialize_mutation_input_class(input_cls.__name__, input_cls)
            return input_cls

        @classmethod
        def resolve_sync(
            cls,
            info: Any,
            *,
            data: Any,
            id: Any,  # noqa: A002
        ) -> Any:
            """The sync register entry: the shared skeleton with the password step pair."""
            del id  # create-only: the field dispatcher always passes UNSET.
            return _run_register_pipeline_sync(cls, info, data)

        @classmethod
        async def resolve_async(
            cls,
            info: Any,
            *,
            data: Any,
            id: Any,  # noqa: A002
        ) -> Any:
            """The async twin: the SAME sync body in one ``sync_to_async`` boundary."""
            del id  # create-only: the field dispatcher always passes UNSET.
            return await run_in_one_sync_boundary(_run_register_pipeline_sync, cls, info, data)

    return Register


def register_mutation(
    *,
    permission_classes: Any = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Any = (),
) -> Any:
    """Return the ``register(data: RegisterInput!)`` mutation field (Decision 6).

    Synthesizes (once, cached through the auth declaration ledger) the
    ``Register`` rider and exposes it through the unchanged
    ``DjangoMutationField``. EVERY call - cached or not - re-records the rider
    into BOTH declaration ledgers (the mutation ledger, so ``bind_mutations()``
    re-binds it after a ``registry.clear()``; the auth ledger, so the Decision-8
    register-arm validation still covers it on a post-clear second finalize),
    identity-deduped on both. A second call with a DIFFERENT
    ``permission_classes`` raises ``ConfigurationError`` (the fixed
    ``RegisterInput`` / ``RegisterPayload`` names cannot serve two
    permission-specialized classes); presentation kwargs never enter that key.
    """
    rider_cls = _declare_auth_surface(
        "register",
        "Register",
        permission_classes,
        _synthesize_register_rider,
    )
    # The every-call re-record on BOTH ledgers (identity-deduped): a live ledger
    # is a no-op; a drained one re-appends, so the rider - and its auth-specific
    # bind validation - survive the complete-reload fixtures (Revision 4 P2).
    record_mutation_declaration(rider_cls)
    register_auth_mutation(rider_cls)
    return DjangoMutationField(
        rider_cls,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )


def _resolve_user_primary_or_raise(user_model: type, surfaces: list[str]) -> type:
    """Resolve the user model's primary ``DjangoType``, or raise the auth-specific fix.

    Rides ``registry.get(user_model)`` - the SAME getter ``_resolve_primary_type``
    uses, so "what counts as a registered primary" stays single-sited (D16);
    ``registry.types_for`` is consulted only to split the no-registered-type
    message from the multiple-types-without-primary ambiguity. Fired from
    ``bind_auth_mutations()`` BEFORE ``bind_mutations()`` so the register rider's
    generic ``_resolve_primary_type`` message can never pre-empt this actionable
    one (Decision 8), and only when a user-typed surface was actually declared
    (the surface-keyed bind - a logout-only ledger never reaches this lookup).
    """
    primary = registry.get(user_model)
    if primary is not None:
        return primary
    factories = " / ".join(_SURFACE_FACTORY_NAMES[surface] for surface in surfaces)
    if registry.types_for(user_model):
        raise ConfigurationError(
            f"auth {factories} declared, but the user model {user_model.__name__} has multiple "
            "registered DjangoTypes and no declared primary; set Meta.primary = True on one of "
            "them so the auth user type is unambiguous.",
        )
    raise ConfigurationError(
        f"auth {factories} declared with no registered DjangoType for the user model "
        f"{user_model.__name__}; declare a DjangoType with Meta.model = get_user_model() "
        "(mark it Meta.primary = True if the model has several types) so the auth surface "
        "has a user type to return.",
    )


def bind_auth_mutations() -> None:
    """Bind the declared auth surfaces at phase 2.5 (spec-040 Decision 9).

    Called by ``types/finalizer.py`` AFTER the pre-bind emit-ledger reset and
    BEFORE ``bind_mutations()`` (the pinned slot - the ordering that keeps the
    register-arm user-type validation reachable, Decision 8). **Surface-keyed**:
    the ledger records which of the four surfaces was declared and the bind
    performs only the work those surfaces need - the user primary is resolved at
    most once and only when a user-typed surface (``login`` / ``register`` /
    ``current_user``) was declared, so a logout-only schema binds with no user
    type registered at all and a partial schema emits no orphan sibling payloads.
    Payload materialization rides the ONE ``build_payload_type`` builder + the
    existing ``mutations.inputs`` emit ledger (D5); the ``current_user`` return
    alias rides the ``auth.queries`` namespace trio (D13). Everything lands
    before ``strawberry.Schema(...)`` resolves the fields' lazy forward-refs.
    """
    declared = iter_auth_mutations()
    if not declared:
        return
    by_surface = {declaration._auth_surface: declaration for declaration in declared}
    user_typed = [
        surface for surface in ("login", "register", "current_user") if surface in by_surface
    ]
    primary = None
    if user_typed:
        primary = _resolve_user_primary_or_raise(get_user_model(), user_typed)

    login_holder = by_surface.get("login")
    if login_holder is not None:
        login_holder._primary_type = primary
        payload_cls = build_payload_type(
            "Login",
            object_type=primary,
            object_slot=payload_object_slot(primary),
        )
        materialize_mutation_input_class(payload_cls.__name__, payload_cls)
        login_holder._payload_type_name = payload_cls.__name__

    logout_holder = by_surface.get("logout")
    if logout_holder is not None:
        payload_cls = build_payload_type("Logout", object_type=None, object_slot=None)
        materialize_mutation_input_class(payload_cls.__name__, payload_cls)
        logout_holder._payload_type_name = payload_cls.__name__

    current_user_holder = by_surface.get("current_user")
    if current_user_holder is not None:
        current_user_holder._primary_type = primary
        # Function-local import: ``queries`` imports this module, so the edge back
        # must stay lazy - and the alias namespace only matters when the consumer
        # imported ``current_user`` (which imported ``queries``).
        from .queries import CURRENT_USER_ALIAS_NAME, materialize_current_user_alias

        materialize_current_user_alias(CURRENT_USER_ALIAS_NAME, primary)
    # ``register`` needs no auth-side emit work: the rider is an ordinary
    # ``DjangoMutation``, so ``bind_mutations()`` (next in the pinned order)
    # materializes its ``RegisterInput`` / ``RegisterPayload``; this bind's
    # contribution is the register-arm user-type validation above.
