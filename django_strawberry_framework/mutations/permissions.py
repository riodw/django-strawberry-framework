"""Shared mutation authorization: permission execution, model permissions, and model-less deny-by-default.

The write side's default permission class (spec-036 Decision 15 / AR-H3). It is a
**first-class, separate contract from row visibility** (``get_queryset`` +
``apply_cascade_permissions``, spec-036 Decision 10): ``get_queryset`` answers "may
this caller *see* this row", this class answers "may this caller *write* it" -
"can view" is never "can write". It maps the mutation ``operation`` to a Django
model permission codename (``create -> add``, ``update -> change``,
``delete -> delete``) and checks it against ``info.context.request.user`` via
``user.has_perm``; an anonymous / unauthenticated user holds no perms and is
denied by default (the safe default that makes "anonymous cannot mutate"
derivable from the foundation rather than from per-schema resolver workarounds).

Enforcement is wired into the mutation resolver pipeline: the resolver invokes
``Meta.permission_classes`` / ``check_permission`` at the authorization step
(spec-036 Decision 8 step 3), so ``has_permission`` runs on every ``/graphql/``
write. Each hook must be a SYNC method returning a ``bool`` - an ``async def``
returns a truthy coroutine and any non-bool is truthy too, so both are rejected
outright rather than silently treated as "allow" (an authorization bypass).

The ``info.context.request.user`` extraction reuses
``utils/permissions.py::request_from_info`` (the read-side request resolver the
filter / order permission pipelines use) so user resolution stays single-sited
across read and write.
"""

from __future__ import annotations

from typing import Any

from ..exceptions import ConfigurationError
from ..utils.permissions import request_from_info
from ..utils.querysets import reject_async_in_sync_context

# The one mapping spec-036 Decision 15 names: a mutation ``operation`` to the
# Django model-permission action verb. Single-sited so the resolver reuses
# it if it needs the action verb (e.g. for an error message). Django's own
# ``Permission`` codename scheme is ``<action>_<model_name>`` (the DRF
# ``DjangoModelPermissions`` ``perms_map`` shape).
_OPERATION_PERMISSION_ACTION: dict[str, str] = {
    "create": "add",
    "update": "change",
    "delete": "delete",
}

# The recourse appended to a ``SyncMisuseError`` raised when a permission hook
# (``check_permission`` / a ``permission_classes`` entry's ``has_permission``)
# returns a coroutine. Write authorization runs synchronously in the same sync
# pipeline (spec-036 Decision 15), so an async permission hook can never be
# awaited - and silently treating its truthy coroutine as "allow" is an
# authorization BYPASS (feedback - async permission bypass). Consumed only by
# ``_require_sync_bool_auth_result``, the single guard the three write-auth
# result seams share (``has_permission`` / ``check_permission`` /
# ``user.has_perm``), so the wording cannot drift between them.
_PERMISSION_ASYNC_RECOURSE = (
    "A DjangoMutation runs its permission check synchronously, so it cannot await "
    "an async permission hook; redefine has_permission / check_permission as a sync "
    "method returning a bool, and ensure user.has_perm / auth backends return a bool."
)


def _require_sync_bool_auth_result(value: Any, *, owner: str, method: str) -> bool:
    """Return a sync authorization bool; reject awaitables and non-bools (BETA-055).

    The ONE write-authorization result contract the three sync seams share:
    ``has_permission``, ``check_permission``, and ``user.has_perm``. Each must
    return an actual ``bool``; a truthy coroutine or any other non-bool would
    silently read as "allow" under a truthiness test - an authorization bypass.
    Async rejection reuses ``reject_async_in_sync_context`` with the shared
    ``_PERMISSION_ASYNC_RECOURSE`` so the wording cannot drift between seams.
    """
    allowed = reject_async_in_sync_context(
        value,
        owner=owner,
        method=method,
        context="mutation",
        recourse=_PERMISSION_ASYNC_RECOURSE,
    )
    if not isinstance(allowed, bool):
        raise ConfigurationError(
            f"{owner}.{method} must return a bool; got {allowed!r}. "
            "Authorization results are never coerced from truthiness.",
        )
    return allowed


def run_permission_classes(
    mutation_self: Any,
    info: Any,
    operation: str,
    data: Any,
    instance: Any,
) -> bool:
    """Run every ``Meta.permission_classes`` entry; deny as soon as one denies (DRY review A5).

    The single body behind the default ``check_permission`` on BOTH write-flavor
    bases (``DjangoMutation`` and the plain ``DjangoFormMutation``, which is not a
    ``DjangoMutation`` subclass; the serializer flavor inherits the model's).
    An authorization-seam fork is the exact "fix one side, miss the other" bug
    class this promotion closes. Each entry's ``has_permission(info, mutation,
    operation, data, instance)`` result runs through
    ``_require_sync_bool_auth_result``: an ``async def has_permission`` returns a
    TRUTHY coroutine, so a naive bool test would silently treat an async
    deny-check as ALLOW - an authorization bypass; the coroutine is closed and
    raised as a ``SyncMisuseError`` instead. Returns ``False`` on the first
    denial, ``True`` only when all allow.
    """
    meta = type(mutation_self)._mutation_meta
    for permission_class in meta.permission_classes:
        allowed = _require_sync_bool_auth_result(
            permission_class().has_permission(
                info,
                type(mutation_self),
                operation,
                data,
                instance,
            ),
            owner=permission_class.__name__,
            method="has_permission",
        )
        if not allowed:
            return False
    return True


class DjangoModelPermission:
    """Default write-authorization: require the Django ``add`` / ``change`` / ``delete`` perm.

    The default member of ``Meta.permission_classes`` (spec-036 Decision 15) and
    the documented base consumers subclass for a custom class-based check. The
    ``has_permission`` signature matches the seam the spec pins
    (``has_permission(info, mutation, operation, data, instance)``); the
    resolver invokes it once per operation.

    A caller is authorized only when ``info.context.request.user`` holds
    ``<app_label>.<action>_<model_name>`` for the operation's action verb. An
    anonymous user (``AnonymousUser`` / ``is_authenticated == False``) holds no
    perms, so ``has_perm`` returns ``False`` and the write is denied - the safe
    default.
    """

    def has_permission(
        self,
        info: Any,
        mutation: type,
        operation: str,
        data: Any,
        instance: Any = None,
    ) -> bool:
        """Return whether the request user holds the model perm for ``operation``.

        ``mutation`` is the ``DjangoMutation`` subclass; its resolved model is
        read via ``mutation._resolve_model(mutation.Meta)`` (the shared
        ``_resolve_model`` seam), so the form / serializer flavors that resolve a
        model without ``Meta.model`` authorize through the same default. ``data``
        and ``instance`` are accepted for the spec signature (an object-level
        subclass can inspect them); the default model-permission check ignores
        them.
        """
        del data, instance  # accepted for the spec signature; unused by the model check.
        request = request_from_info(info, family_label="DjangoMutation")
        user = getattr(request, "user", None)
        if user is None:
            return False
        model = mutation._resolve_model(mutation.Meta)
        action = _OPERATION_PERMISSION_ACTION[operation]
        codename = f"{model._meta.app_label}.{action}_{model._meta.model_name}"
        # ``user.has_perm`` is sync Django auth; an awaitable / non-bool return
        # is the same authorization-bypass class ``_require_sync_bool_auth_result``
        # closes for ``has_permission`` / ``check_permission`` (BETA-055).
        return _require_sync_bool_auth_result(
            user.has_perm(codename),
            owner=type(user).__name__,
            method="has_perm",
        )


class DenyAll:
    """Deny-by-default write authorization for a model-less plain ``DjangoFormMutation``.

    A plain ``DjangoFormMutation`` has no model, so the
    ``DjangoModelPermission`` default cannot apply to it: that class reads the
    model via ``mutation._resolve_model(mutation.Meta)`` and maps the operation to
    an ``add`` / ``change`` / ``delete`` codename, neither of which a model-less
    ``"form"`` mutation provides (it would raise at request time, not deny). So an
    *unset* ``Meta.permission_classes`` on a plain form installs this class
    instead (spec-038 Decision 11): it **denies every request**, keeping the
    safe-by-default posture ``036`` established rather than silently shipping an
    unauthenticated write surface.

    A public plain-form write is the explicit opt-in ``Meta.permission_classes =
    []`` (the ``036`` AllowAny posture - an empty class list authorizes every
    request, because ``check_permission`` iterates no classes). This class inspects
    **no** model metadata, so it is safe for the model-less flavor; its
    ``has_permission`` signature matches the seam every permission class exposes.

    Internal-by-design: the plain form installs it as a default, so a consumer
    never names it (deny is the default; ``[]`` opts in to public). It is not part
    of the pinned public ``__all__`` surface (which widens only via a spec).
    """

    def has_permission(
        self,
        info: Any,
        mutation: type,
        operation: str,
        data: Any,
        instance: Any = None,
    ) -> bool:
        """Always deny: a plain form with no explicit ``permission_classes`` is closed."""
        del info, mutation, operation, data, instance  # a closed default reads none of them.
        return False
