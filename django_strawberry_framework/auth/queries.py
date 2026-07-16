"""The ``current_user()`` query-field factory + its return-alias namespace (spec-040).

``current_user()`` returns the nullable session actor - ``request.user`` when
authenticated, ``null`` otherwise - typed as the consumer's primary user
``DjangoType`` through a bind-materialized ``strawberry.lazy`` alias
(spec-040 Decision 7). The resolver performs NO queryset work: no
``get_queryset`` re-run (a directory-shaped visibility hook must not make ``me``
return ``null`` for a logged-in user - the actor-not-lookup rule, D-N1) and no
re-fetch (the middleware already loaded the row, lazily).

The ``CurrentUserAlias`` module global is an EMIT artifact owned by a
``make_input_namespace`` trio (the D13 reuse directive - the blessed
parked-global lifecycle, never a hand-rolled ``setattr`` / ``delattr`` pair):
``bind_auth_mutations()`` pins the alias to the resolved user primary each
finalize, and the trio's ``clear_fn`` is this module's pre-bind
``register_subsystem_clear`` row, so the ledger is empty before each
re-materialize and a reload's different ``UserType`` class object never trips
the distinct-class collision guard.
"""

from __future__ import annotations

import functools
from typing import Any

from ..mutations.fields import _lazy_ref
from ..registry import register_subsystem_clear
from ..utils.inputs import make_input_namespace
from ..utils.permissions import request_from_info
from .mutations import (
    _AUTH_FAMILY_LABEL,
    _authenticated_actor_or_none,
    _declare_fixed_auth_surface,
    _make_auth_field,
)

AUTH_QUERIES_MODULE_PATH = "django_strawberry_framework.auth.queries"

# The bind-materialized return-alias name the injected ``current_user`` return
# annotation forward-references; Strawberry resolves it to the concrete consumer
# ``UserType`` at schema build, so the SDL reads ``me: UserType``.
CURRENT_USER_ALIAS_NAME = "CurrentUserAlias"

# The alias-namespace lifecycle trio (spec-040 D13): ``materialize_current_user_alias``
# pins the resolved user primary as this module's ``CurrentUserAlias`` global via
# the blessed ``materialize_generated_input_class`` parked-global path;
# ``clear_current_user_alias_namespace`` empties the ledger.
(
    _current_user_alias_names,
    materialize_current_user_alias,
    clear_current_user_alias_namespace,
) = make_input_namespace(AUTH_QUERIES_MODULE_PATH, _AUTH_FAMILY_LABEL)

# The alias namespace is a genuine EMIT ledger, so its clear is a canonical
# PRE-BIND row (spec-040 Decision 9): the finalizer's pre-bind reset (and
# ``TypeRegistry.clear()``) drain it before ``bind_auth_mutations()`` re-pins the
# alias. The auth declaration ledger, by contrast, registers a full-clear-only
# callback. This optional owner registers only when the auth subsystem is loaded.
register_subsystem_clear(
    clear_current_user_alias_namespace,
    owner="auth.current_user_alias",
    before_bind=True,
)


def _current_user_resolve_body(holder_cls: type, info: Any) -> Any:
    """Return the session actor (or ``None``) after the permission gate (Decision 7).

    The gate runs FIRST - its ``instance`` argument is the authenticated request
    user or ``None``, computed here (forcing the lazy ``SimpleLazyObject`` - on
    the async path this body already runs inside the one ``sync_to_async``
    boundary, so the forced ORM touch never raises ``SynchronousOnlyOperation``).
    A denial is a top-level ``GraphQLError``; only after the gate passes does the
    nullable-return rule apply (allowed-but-anonymous -> ``null``, never an
    error). The AllowAny default gates nothing; a consumer who wants ``me`` to
    require authentication supplies an ``IsAuthenticated``-style class, which
    denies the anonymous caller with the ``GraphQLError`` instead of ``null``.
    """
    from ..mutations import resolvers

    request = request_from_info(info, family_label=_AUTH_FAMILY_LABEL)
    # The Channels adapter returns ``None`` when its scope has no auth middleware;
    # a bare HttpRequest without AuthenticationMiddleware has no ``user`` attribute.
    # Both are anonymous under this field's nullable-return contract - owned by
    # ``_authenticated_actor_or_none`` (shared with ``logout``'s ``ok`` capture).
    actor = _authenticated_actor_or_none(request)
    resolvers.authorize_or_raise(holder_cls, info, "current_user", None, instance=actor)
    return actor


def current_user(
    *,
    permission_classes: Any = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Any = (),
) -> Any:
    """Return the nullable session-actor query field (spec-040 Decision 7).

    The read-side member of the auth surface: a query FIELD (not a mutation)
    returning the consumer's primary user ``DjangoType`` or ``null`` for an
    anonymous request - nullable-by-contract (an anonymous session is an expected
    state, not an error), with no ``get_queryset`` re-run and no envelope (there
    is no ``ok`` / ``errors`` slot; ``me`` returns the user type directly).
    Declared through the same fixed-field path as ``login`` / ``logout`` (the
    ``CurrentUser`` permission holder, the AllowAny default, the
    one-declaration-per-process conflict rule) and typed through the
    bind-materialized ``CurrentUserAlias`` lazy forward-ref.
    """
    holder_cls = _declare_fixed_auth_surface("current_user", "CurrentUser", permission_classes)
    return _make_auth_field(
        resolve_body=functools.partial(_current_user_resolve_body, holder_cls),
        arguments=[],
        return_annotation=_lazy_ref(CURRENT_USER_ALIAS_NAME, AUTH_QUERIES_MODULE_PATH) | None,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
