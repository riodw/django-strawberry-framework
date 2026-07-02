"""Planned auth query factory for spec-040."""

from __future__ import annotations

from typing import Any

from ..registry import register_subsystem_clear
from ..utils.inputs import make_input_namespace

AUTH_QUERIES_MODULE_PATH = "django_strawberry_framework.auth.queries"
(
    _current_user_alias_names,
    materialize_current_user_alias,
    clear_current_user_alias_namespace,
) = make_input_namespace(AUTH_QUERIES_MODULE_PATH, "AuthMutation")

# TODO(spec-040 Slice 2): ``bind_auth_mutations()`` must call
# ``materialize_current_user_alias("CurrentUserAlias", primary_type)`` rather than
# setting this module global by hand. The alias is an emit artifact, so this clear
# belongs to the pre-bind reset; the auth declaration ledger still clears only
# through ``TypeRegistry.clear``.
register_subsystem_clear(AUTH_QUERIES_MODULE_PATH, "clear_current_user_alias_namespace")


def current_user(
    *,
    permission_classes: Any = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Any = (),
) -> Any:
    """Return the planned nullable session-actor query field."""
    # TODO(spec-040 Slice 2): implement as a fixed field factory sharing the auth
    # resolver/signature helper with login/logout. Pseudocode: normalize
    # ``permission_classes`` with AllowAny as the unset default through the shared
    # fixed-field declaration helper, reject a conflicting second declaration,
    # record the auth declaration, inject a lazy ``CurrentUserAlias | None`` return
    # annotation via the shared ``_lazy_ref``/signature helper, and return
    # ``strawberry.field`` with the passed field kwargs. The resolver reads the
    # request via ``request_from_info``, computes ``instance`` as the authenticated
    # request user or ``None``, gates through ``authorize_or_raise`` with operation
    # ``"current_user"``, and returns that instance. The async path must compute
    # ``instance=request.user`` and run the gate inside the same sync worker as the
    # lazy-user access; no ``get_queryset`` or optimizer re-fetch belongs on this
    # actor-returning surface.
    del permission_classes, description, deprecation_reason, directives
    raise NotImplementedError("spec-040 Slice 2 current_user is not implemented")
