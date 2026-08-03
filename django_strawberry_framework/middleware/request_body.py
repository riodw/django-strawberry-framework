"""The package's raw-request-body boundary, expressed as a ``MIDDLEWARE`` entry.

``views.py`` owns the boundary itself - the cumulative body cap (spec-046
Decision 7) and the header-only wire-encoding refusals (Decision 9). What this
module owns is *where in the request lifecycle* that boundary runs, for
deployments that install it::

    MIDDLEWARE = [
        ...,
        "django_strawberry_framework.middleware.request_body"
        ".GraphQLRequestBodyBoundaryMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        ...,
    ]

Why a middleware entry is the right owner of the ordering
---------------------------------------------------------

Django's ``CsrfViewMiddleware.process_view`` reads
``request.POST.get("csrfmiddlewaretoken", "")`` on every cookie-bearing POST, and
on a multipart request that single read is what invokes ``MultiPartParser`` and
the project's upload handlers - before the view runs. A cap that runs after
something else has already parsed the body is not a gate, so the package's
boundary has to precede that read.

Doing it from inside the view requires exempting the view's callback from the
CSRF middleware and re-entering CSRF from the view, and that re-entry can only
name a CSRF implementation the package chooses. A deployment whose
``MIDDLEWARE`` names a ``CsrfViewMiddleware`` **subclass** - one that strengthens
token binding, adds a tenant check, or logs failures - would then have its own
class silently replaced by Django's base implementation on the GraphQL endpoint
alone. That is a policy substitution, and no view-local decorator can avoid it,
because the configured class is a property of the middleware chain.

So the ordering moves into the chain. This middleware runs the whole boundary
from ``process_view`` - which Django calls after URL resolution and before any
later middleware's ``process_view``, hence before the CSRF middleware's - and,
for the duration of a request it is handling, cancels the CSRF exemption the
package view's callback carries (:data:`_CSRF_ORDERING_EXEMPTION`). The
configured CSRF middleware, whatever class it is, then runs in full on every
request that survives the boundary.

The exemption is a lazily-evaluated object rather than the usual ``True`` for
exactly that reason: whether the ordering is supplied by the chain is not known
when a URLconf is imported, and a deployment must not have to state the same fact
twice. Where this middleware is installed the exemption is ``False`` and only the
configured CSRF middleware runs; where it is not, the exemption is ``True`` and
the view's own boundary-then-CSRF re-entry behaves exactly as it did before this
module existed. Both arrangements enforce CSRF and both enforce the cap; they
differ only in which class performs the check.

Ordering is verified rather than documented: a chain that lists this middleware
*after* a ``CsrfViewMiddleware`` would put the parse back in front of the cap
while looking correct, so :meth:`GraphQLRequestBodyBoundaryMiddleware.__init__`
refuses it with a ``ConfigurationError`` at startup instead.

What it deliberately does not do
--------------------------------

It holds no policy of its own: the limit, the refusal statuses, and the wire
reasons all stay in ``views.py``, and this module reaches them by instantiating
the resolved view exactly as ``View.as_view`` does. It recognizes a package view
by one marker attribute stamped on the callback (:data:`_BOUNDARY_MARKER`), never
by importing the view classes, so no non-package view is touched and the
dependency runs one way only. And it translates the boundary's
``HTTPException`` into the same ``text/plain`` response upstream's ``dispatch``
produces, so the wire shape of a refusal does not depend on which side of the
CSRF check refused it.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from cross_web import HTTPException
from django.conf import settings
from django.http import HttpResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.module_loading import import_string

from django_strawberry_framework.exceptions import ConfigurationError

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponseBase

__all__ = ("GraphQLRequestBodyBoundaryMiddleware",)


#: Stamped on the callback ``_RequestBodyBoundaryMixin.as_view`` returns, and the
#: only thing that makes a resolved view a package view as far as this module is
#: concerned. An attribute rather than an ``issubclass`` check because the
#: dependency has to run one way: ``views.py`` imports this module for the
#: exemption object, so this module must never import ``views.py``.
_BOUNDARY_MARKER = "graphql_request_body_boundary"

#: Stamped on a request whose boundary this middleware has already run, so the
#: view does not measure the same body twice. Read by both package views at the
#: top of ``run``.
_BOUNDARY_ENFORCED = "graphql_request_body_boundary_enforced"

#: True for the duration of a request this middleware is handling - the one fact
#: :class:`_CsrfOrderingExemption` needs and the one the view callback cannot
#: carry, since a callback attribute is process-wide while installation is a
#: property of the chain a request is travelling through. A ``ContextVar`` rather
#: than a thread local so the async chain sees it too, and it is set and reset
#: around the downstream call so it can never leak into an unrelated request.
_boundary_middleware_active: ContextVar[bool] = ContextVar(
    "django_strawberry_framework_boundary_middleware_active",
    default=False,
)


class _CsrfOrderingExemption:
    """The package view callback's ``csrf_exempt`` value: true only when needed.

    ``CsrfViewMiddleware.process_view`` consults the mark as
    ``if getattr(callback, "csrf_exempt", False)``, so the value is read for its
    truthiness at request time - which is what lets one object answer the
    question the package actually has to answer: *does something else already
    order the body boundary ahead of the CSRF check?*

    When this module's middleware is installed the answer is yes, the exemption
    is false, and the deployment's own ``CsrfViewMiddleware`` (or subclass) runs
    normally, after the boundary. When it is not installed the answer is no, the
    exemption is true, and the view keeps its own boundary-then-CSRF re-entry -
    the arrangement that predates this middleware and that a deployment which has
    not changed its ``MIDDLEWARE`` must keep unchanged.

    It is never a bypass in either state: exactly one complete CSRF check runs on
    every request that gets past the boundary.
    """

    def __bool__(self) -> bool:
        """Whether the view still has to supply the ordering itself."""
        return not _boundary_middleware_active.get()


#: One instance, shared by every package view callback - it carries no per-view
#: state, and its answer is a property of the chain rather than of the mount.
_CSRF_ORDERING_EXEMPTION = _CsrfOrderingExemption()


#: The ``ConfigurationError`` text for a chain that would defeat the ordering.
_MISORDERED_MIDDLEWARE_MESSAGE = (
    "GraphQLRequestBodyBoundaryMiddleware must appear BEFORE Django's CsrfViewMiddleware in "
    "MIDDLEWARE: the CSRF check reads request.POST, which parses a multipart body, so a "
    "request-body boundary listed after it can no longer run before the parse it exists to "
    "prevent."
)


class GraphQLRequestBodyBoundaryMiddleware:
    """Run the package views' request-body boundary from the middleware chain.

    Install it immediately before the project's ``CsrfViewMiddleware`` entry. See
    the module docstring for why the ordering is a middleware question rather than
    a view-local one, and for what changes on a mount when it is installed.

    Every request that is not a package view's is passed through untouched, at the
    cost of one ``getattr`` in ``process_view``.
    """

    #: Declared for both chains so Django adapts nothing: an async deployment
    #: keeps its coroutine view dispatch, and ``__acall__`` awaits downstream
    #: rather than handing a coroutine to a synchronous caller.
    sync_capable = True
    async_capable = True

    def __init__(self, get_response: Callable[[HttpRequest], Any]) -> None:
        """Bind the downstream chain and refuse a chain that cannot deliver the ordering."""
        self.get_response = get_response
        _require_boundary_before_csrf()
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    def __call__(self, request: HttpRequest) -> Any:
        """Mark the boundary as chain-supplied for this request, then call downstream.

        The mark spans the downstream call rather than the ``process_view`` hook
        alone, because it is read by the CSRF middleware - which may be *any*
        later entry in the chain - and reset in a ``finally`` so a raising view
        cannot leave it set for whatever the worker handles next.
        """
        if iscoroutinefunction(self):
            return self.__acall__(request)
        token = _boundary_middleware_active.set(True)
        try:
            return self.get_response(request)
        finally:
            _boundary_middleware_active.reset(token)

    async def __acall__(self, request: HttpRequest) -> Any:
        """The async twin of :meth:`__call__` - the ``await`` is the whole difference.

        Separate rather than shared because the reset has to happen after the
        downstream response exists: returning the coroutine from a synchronous
        ``finally`` would reset the mark before the CSRF middleware ever read it.
        """
        token = _boundary_middleware_active.set(True)
        try:
            return await self.get_response(request)
        finally:
            _boundary_middleware_active.reset(token)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., Any],
        view_args: tuple[Any, ...],  # noqa: ARG002 - Django's own process_view signature
        view_kwargs: dict[str, Any],  # noqa: ARG002 - Django's own process_view signature
    ) -> HttpResponseBase | None:
        """Run a package view's body boundary here, before any later ``process_view``.

        The boundary itself is the view's, reached through an instance built the
        way ``View.as_view`` builds one, so the limit that applies is the mount's
        own ``max_request_body_bytes`` and this module states no policy. A refusal
        becomes the same ``text/plain`` response upstream's ``dispatch`` produces
        for the identical ``HTTPException``, so a client cannot tell from the
        response which side of the CSRF check refused it.
        """
        if not getattr(view_func, _BOUNDARY_MARKER, False):
            return None
        view = view_func.view_class(**view_func.view_initkwargs)
        try:
            view._enforce_request_boundary(request)
        except HTTPException as exc:
            return HttpResponse(
                content=exc.reason,
                status=exc.status_code,
                content_type="text/plain",
            )
        setattr(request, _BOUNDARY_ENFORCED, True)
        return None


def _require_boundary_before_csrf() -> None:
    """Raise ``ConfigurationError`` when a CSRF entry precedes this middleware.

    Read off ``settings.MIDDLEWARE`` at instantiation - which is chain-build time,
    so a misordered deployment fails at startup rather than on the first
    multipart request. Entries are resolved and compared by class rather than by
    dotted path, so a subclass of either middleware is recognized as what it is;
    a non-class entry (a function middleware) is neither and is skipped.

    Nothing is raised when the chain contains no CSRF middleware at all: there is
    then no read to run behind, and the package view's own CSRF continuation
    still protects the endpoint.
    """
    boundary_index = csrf_index = None
    for index, path in enumerate(settings.MIDDLEWARE):
        entry = import_string(path)
        if not isinstance(entry, type):
            continue
        if issubclass(entry, GraphQLRequestBodyBoundaryMiddleware):
            boundary_index = index
        elif issubclass(entry, CsrfViewMiddleware) and csrf_index is None:
            csrf_index = index
    if boundary_index is None or csrf_index is None or csrf_index > boundary_index:
        return
    raise ConfigurationError(_MISORDERED_MIDDLEWARE_MESSAGE)
