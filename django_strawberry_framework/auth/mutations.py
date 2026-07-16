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

import functools
from typing import Any

import strawberry
from django.contrib import auth
from django.contrib.auth import get_user_model
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


async def _resolve_auth_async(resolve_body: Any, info: Any, kwargs: dict[str, Any]) -> Any:
    """Run one auth field's gate-then-session-work body in ONE sync worker (spec-040 D17).

    The single async boundary the three fixed auth fields share: the WHOLE
    ``resolve_body`` - request resolution, the permission gate (whose
    ``instance=request.user`` argument forces the ``SimpleLazyObject`` as it is
    computed, a sync ORM touch - the Decision-10 async-gate fix), and the session
    work - runs inside one ``sync_to_async(thread_sensitive=True)`` call via the
    shared ``run_in_one_sync_boundary`` primitive. The ``SyncMisuseError``
    discipline is unaffected: the worker is itself a sync context, so an ``async
    def has_permission`` is still rejected there, never silently allowed.
    """
    return await run_in_one_sync_boundary(resolve_body, info, **kwargs)


def _make_auth_field(
    *,
    resolve_body: Any,
    arguments: list[tuple[str, Any]],
    return_annotation: Any,
    description: str | None,
    deprecation_reason: str | None,
    directives: Any,
) -> Any:
    """Build one fixed auth field around a sync gate-then-session-work body.

    The ONE auth field-construction helper the three fixed factories share
    (spec-040 D12 / P1 / P2): the dispatcher resolves sync-vs-async per call via
    ``in_async_context()`` (the ``DjangoMutationField`` runtime dispatch), the
    async path wraps ``resolve_body`` in the single shared boundary, and the
    injected ``__signature__`` / ``__annotations__`` (the keyword-only GraphQL
    args + the ``strawberry.lazy`` return forward-ref, unresolved at class-body
    time) ride the promoted ``mutations/fields.py`` machinery -
    ``build_lazy_field_signature`` over ``_lazy_ref``-built refs - never a
    re-spelled copy. ``arguments`` is the ordered ``(name, annotation)`` list of
    keyword-only GraphQL args (empty for ``logout`` / ``me``).
    """

    def _resolve(root: Any, info: Any, **kwargs: Any) -> Any:  # noqa: ARG001
        if in_async_context():
            return _resolve_auth_async(resolve_body, info, kwargs)
        return resolve_body(info, **kwargs)

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


def _login_resolve_body(
    holder_cls: type,
    info: Any,
    *,
    username: str,
    password: str,
) -> Any:
    """Authenticate + establish the session behind the envelope (spec-040 Decision 5).

    Gate first (``data`` carries the attempted username - NEVER the password - so
    an account-scoped rate-limit / lockout gate can key on it; a denial is the
    top-level ``GraphQLError`` and credential checking is never reached), then the
    upstream-borrowed semantics: ``authenticate(request, username=, password=)``,
    ``None`` -> the ONE non-field-keyed envelope entry (built via the
    ``field_error("", ...)`` empty-path leaf ctor, which owns the ``"__all__"``
    sentinel - the D8 reuse directive), success -> ``auth.login`` then the user in
    the payload's uniform slot. The payload user is the RAW ``authenticate()``
    instance - no ``get_queryset`` re-run (the actor-not-lookup rule, D-N1) and no
    optimizer re-fetch (deliberately asymmetric with ``register``'s G2-planned
    node).
    """
    from ..mutations import resolvers
    from ..utils.write_values import unencodable_text_error

    request = request_from_info(info, family_label=_AUTH_FAMILY_LABEL)
    resolvers.authorize_or_raise(
        holder_cls,
        info,
        "login",
        {"username": username},
        instance=None,
    )
    payload_cls = resolvers.payload_cls_for(holder_cls)
    slot = payload_object_slot(holder_cls._primary_type)
    # A credential carrying a lone surrogate code point (a GraphQL ``String`` can,
    # via a JSON ``\uXXXX`` escape) is not UTF-8 encodable, so handing it to
    # ``authenticate`` crashes it into a raw ``UnicodeEncodeError`` - the DB
    # ``USERNAME_FIELD`` lookup for the username, the password hasher's ``.encode()``
    # for the password - a top-level GraphQL error instead of the pinned failed-login
    # envelope. Such a credential authenticates no one, so it is short-circuited to
    # the SAME undifferentiated envelope (never a distinct field-keyed error, which
    # would break the byte-identical enumeration guard), reusing the ONE write-side
    # storability preflight so "unstorable text" stays single-sited with the shared
    # scalar decode (``decode_scalar_leaf``) every other input runs through.
    unstorable = (
        unencodable_text_error("username", username) is not None
        or unencodable_text_error("password", password) is not None
    )
    user = None if unstorable else auth.authenticate(request, username=username, password=password)
    if user is None:
        # No error code, deliberately: the user-facing failed-login contract is
        # ``field: "__all__"`` + the one undifferentiated message ONLY. A code
        # would become public GraphQL surface the moment a consumer keys on it
        # (a breaking change to ever rename), and the spec pins no code.
        error = resolvers.field_error("", _INCORRECT_CREDENTIALS_MESSAGE)
        return resolvers.build_payload(payload_cls, slot, None, [error])
    auth.login(request, user)
    return resolvers.build_payload(payload_cls, slot, user, [])


def _logout_resolve_body(holder_cls: type, info: Any) -> Any:
    """End the session; ``ok`` is whether an authenticated one existed (Decision 5).

    Gate first (denial target reads the holder ``__name__`` - the pinned
    ``"Not authorized to logout Session."`` string), then the upstream-borrowed
    semantics: capture whether the request has an authenticated actor via
    ``_authenticated_actor_or_none`` (the ONE anonymity definition shared with
    ``current_user``), then call Django's ``logout`` unconditionally. A request
    with SessionMiddleware but no AuthenticationMiddleware has no ``user``
    attribute, so the capture treats that shape as anonymous. Teardown still runs
    because an anonymous request can carry session data that logout must flush.
    Session-mutating auth continues to require Django's session transport;
    Channels auth mutations remain outside the verified read-path-only adapter
    contract. Returns the pinned model-less ``{ ok, errors }`` payload with empty
    ``errors``.
    """
    from ..mutations import resolvers

    request = request_from_info(info, family_label=_AUTH_FAMILY_LABEL)
    resolvers.authorize_or_raise(holder_cls, info, "logout", None, instance=None)
    ok = _authenticated_actor_or_none(request) is not None
    auth.logout(request)
    payload_cls = resolvers.payload_cls_for(holder_cls)
    return payload_cls(ok=ok, errors=[])


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
        resolve_body=functools.partial(_login_resolve_body, holder_cls),
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
        resolve_body=functools.partial(_logout_resolve_body, holder_cls),
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
