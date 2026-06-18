"""``DjangoModelPermission`` - the DRF-shaped default write-authorization class (spec-036).

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

**Slice 2 ships the class + its ``has_permission`` body + the export only.** The
*enforcement wiring* - the resolver invoking ``Meta.permission_classes`` /
``check_permission`` at the right pipeline step (spec-036 Decision 8 step 3) - is
Slice 3. Nothing in this slice calls ``has_permission`` from a ``/graphql/``
request; the body is exercised directly by the Slice-2 unit test.

The ``info.context.request.user`` extraction reuses
``utils/permissions.py::request_from_info`` (the read-side request resolver the
filter / order permission pipelines use) so user resolution stays single-sited
across read and write.
"""

from __future__ import annotations

from typing import Any

from ..utils.permissions import request_from_info

# The one mapping spec-036 Decision 15 names: a mutation ``operation`` to the
# Django model-permission action verb. Single-sited so Slice 3's resolver reuses
# it if it needs the action verb (e.g. for an error message). Django's own
# ``Permission`` codename scheme is ``<action>_<model_name>`` (the DRF
# ``DjangoModelPermissions`` ``perms_map`` shape).
_OPERATION_PERMISSION_ACTION: dict[str, str] = {
    "create": "add",
    "update": "change",
    "delete": "delete",
}


class DjangoModelPermission:
    """Default write-authorization: require the Django ``add`` / ``change`` / ``delete`` perm.

    The default member of ``Meta.permission_classes`` (spec-036 Decision 15) and
    the documented base consumers subclass for a custom class-based check. The
    ``has_permission`` signature matches the seam the spec pins
    (``has_permission(info, mutation, operation, data, instance)``); Slice 3's
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
        read via ``mutation._resolve_model(mutation.Meta)`` (the Slice-2
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
        return bool(user.has_perm(codename))
