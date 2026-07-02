"""Planned auth mutation factories for spec-040.

This file is intentionally scaffold-only until the spec-040 slices land. The
TODO blocks below name the source seams the implementation must reuse instead of
forking: declaration ledgers from ``mutations.sets``, payload construction from
``mutations.inputs``, authorization from ``mutations.resolvers``, and request
resolution from ``utils.permissions``.
"""

from __future__ import annotations

from typing import Any

from ..mutations.sets import make_declaration_registry

_AUTH_FAMILY_LABEL = "AuthMutation"
_auth_declaration_registry = make_declaration_registry(_AUTH_FAMILY_LABEL)
register_auth_mutation = _auth_declaration_registry.register
clear_auth_mutation_registry = _auth_declaration_registry.clear
iter_auth_mutations = _auth_declaration_registry.iter_
_auth_declarations = _auth_declaration_registry.store

# TODO(spec-040 Slice 1): route login/logout/current_user fixed-field
# declarations through one helper that normalizes permission classes, rejects a
# different-permission second declaration for the same fixed payload name, records
# via ``register_auth_mutation``, and returns the cached permission holder. Same
# args must be idempotent; different args must raise before Strawberry sees a
# late payload-name collision.


def bind_auth_mutations() -> None:
    """Bind auth declarations in the finalizer phase-2.5 slot."""
    # TODO(spec-040 Slice 1): replace this placeholder with the real auth bind.
    # Pseudocode: snapshot ``iter_auth_mutations()``, resolve
    # ``registry.get(get_user_model())`` once (the same lookup
    # ``_resolve_primary_type`` uses, accepting the single-type/no-explicit-primary
    # case), consult ``registry.types_for`` only to split no-type vs ambiguous-type
    # error messages, then materialize ``LoginPayload`` through
    # ``build_payload_type("Login", object_type=primary,
    # object_slot=payload_object_slot(primary))`` and ``LogoutPayload`` through
    # ``build_payload_type("Logout", object_type=None, object_slot=None)``. Pin
    # both with ``materialize_mutation_input_class`` so payload-name collisions use
    # the existing mutation-input ledger. If ``current_user`` was declared, call
    # ``auth.queries.materialize_current_user_alias("CurrentUserAlias", primary)``;
    # do not hand-roll a module ``setattr`` for that lazy target.
    # Keep this bind before ``bind_mutations()`` so the register rider's missing
    # user-type error is auth-specific rather than the generic mutation bind
    # error. Declaration clearing belongs in ``TypeRegistry.clear()``, while
    # payload clearing rides the existing ``mutations.inputs`` pre-bind row and
    # the current-user alias clearing rides ``auth.queries``' pre-bind row.
    if iter_auth_mutations():
        raise NotImplementedError("spec-040 Slice 1 bind_auth_mutations is not implemented")


def login_mutation(
    *,
    permission_classes: Any = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Any = (),
) -> Any:
    """Return the planned ``login(username:, password:)`` mutation field."""
    # TODO(spec-040 Slice 1): implement as a fixed field factory, not a
    # ``DjangoMutationField`` target. Pseudocode: normalize
    # ``permission_classes`` through ``_validate_permission_classes(...,
    # unset_default=())``; reject conflicting second declarations; record through
    # ``register_auth_mutation``; synthesize the shared ``_make_permission_holder``
    # result; and build the field through the shared auth dispatcher/signature
    # helper that uses ``_lazy_ref("LoginPayload", INPUTS_MODULE_PATH)``. The
    # resolver reads the request with
    # ``request_from_info(info, family_label=_AUTH_FAMILY_LABEL)``, passes only
    # ``{"username": username}`` into ``authorize_or_raise``, calls
    # ``auth.authenticate``, returns a ``field_error("", ...)`` envelope on
    # failure, and calls ``auth.login`` before returning the user payload on
    # success. The async resolver must run gate + authenticate + session mutation
    # inside one ``sync_to_async(thread_sensitive=True)`` boundary.
    del permission_classes, description, deprecation_reason, directives
    raise NotImplementedError("spec-040 Slice 1 login_mutation is not implemented")


def logout_mutation(
    *,
    permission_classes: Any = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Any = (),
) -> Any:
    """Return the planned ``logout`` mutation field."""
    # TODO(spec-040 Slice 1): implement with the model-less payload builder path.
    # Pseudocode: normalize permissions through the same AllowAny helper path as
    # login; reject conflicting second declarations; record through
    # ``register_auth_mutation``; build the shared permission holder with
    # ``_primary_type=None``; gate through ``authorize_or_raise`` with no data or
    # instance; capture ``request.user.is_authenticated`` before teardown; call
    # ``auth.logout`` unconditionally; and return
    # ``LogoutPayload(ok=<captured>, errors=[])``. The holder name must make
    # ``authorize_or_raise``'s no-primary fallback read cleanly in the denial
    # string, and the async resolver uses the same one-boundary helper as login.
    del permission_classes, description, deprecation_reason, directives
    raise NotImplementedError("spec-040 Slice 1 logout_mutation is not implemented")


def register_mutation(
    *,
    permission_classes: Any = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Any = (),
) -> Any:
    """Return the planned ``register(data: RegisterInput!)`` mutation field."""
    # TODO(spec-040 Slice 2): synthesize the cached concrete ``Register`` rider
    # and expose it through ``DjangoMutationField(Register)``. Pseudocode: derive
    # the deduped field tuple from ``USERNAME_FIELD``, ``REQUIRED_FIELDS``, and
    # ``password``; set ``Meta.model`` to ``get_user_model()`` and
    # ``Meta.operation`` to ``"create"``; pin ``input_type_name`` to
    # ``RegisterInput``; override both resolver paths; re-record the cached class
    # into both the mutation and auth ledgers on every same-args factory call; and
    # return ``DjangoMutationField`` with the field kwargs. A different
    # ``permission_classes`` set after the cached class exists must raise
    # ``ConfigurationError`` rather than minting a second fixed-name payload. The
    # decode step must reuse ``_model_decode_step`` with the spec-040 exclusion
    # seam instead of forking the UNSET walk, pop ``password`` before model
    # construction, and carry it as
    # ``(user, m2m_assignments, exclude, raw_password)``. The write step catches
    # ``validate_password(raw_password, user)`` failures at the call site and maps
    # them with ``field_error("password", ...)``, calls ``set_password`` before
    # ``full_clean``, and delegates save errors to ``save_or_field_errors``.
    del permission_classes, description, deprecation_reason, directives
    raise NotImplementedError("spec-040 Slice 2 register_mutation is not implemented")
