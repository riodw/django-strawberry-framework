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
later middleware's ``process_view``, hence before the CSRF middleware's - and
cancels the CSRF exemption the package view's callback carries for the requests
whose boundary it has run. The configured CSRF middleware, whatever class it is,
then runs in full on every request that survives the boundary.

The exemption is a lazily-evaluated object rather than the usual ``True`` for
exactly that reason: whether the ordering is supplied by the chain is not known
when a URLconf is imported, and a deployment must not have to state the same fact
twice. It lives in ``_boundary_ordering.py``
(``::_CsrfOrderingExemption``) together with the two marks, and it is ``False``
for a request this middleware has actually run the boundary for - the narrow
fact, and the load-bearing one, since that is the request whose body is proven
measured. For every other request, including one whose callback this middleware
did not recognize as a package view's, the exemption stays ``True`` and the view's
own boundary-then-CSRF re-entry behaves exactly as it did before this module
existed. Both arrangements enforce CSRF and both enforce the cap; they differ
only in which class performs the check.

Ordering is verified rather than documented: a chain that lists this middleware
*after* a ``CsrfViewMiddleware`` would put the parse back in front of the cap
while looking correct, so :meth:`GraphQLRequestBodyBoundaryMiddleware.__init__`
refuses it with a ``ConfigurationError`` at startup instead.

What it deliberately does not do
--------------------------------

It holds no policy of its own: the limit, the refusal statuses, and the wire
reasons all stay in ``views.py``, and this module reaches them by instantiating
the resolved view exactly as ``View.as_view`` does. It recognizes a package view
by the marker attribute stamped on the callback, by the ``view_class`` /
``view_initkwargs`` bookkeeping behind it, and by the boundary method that
``view_class`` itself has to carry (:func:`_package_view_instance`), never by
importing the view classes - the marker and the boundary method's *name* both
reach this module through ``_boundary_ordering.py`` - so no non-package view is
touched and this module imports neither ``views.py`` nor anything that imports
it. And it translates the boundary's
``HTTPException`` into the same ``text/plain`` response upstream's ``dispatch``
produces, so the wire shape of a refusal does not depend on which side of the
CSRF check refused it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from cross_web import HTTPException
from django.conf import settings
from django.http import HttpResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.module_loading import import_string

from django_strawberry_framework._boundary_ordering import (
    _BOUNDARY_ENFORCED,
    _BOUNDARY_MARKER,
    _BOUNDARY_METHOD,
    _BOUNDARY_MOUNT,
    _BOUNDARY_PREPARED_VIEW,
    _boundary_middleware_request,
)
from django_strawberry_framework.exceptions import ConfigurationError

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponseBase

__all__ = ("GraphQLRequestBodyBoundaryMiddleware",)


#: The ``ConfigurationError`` text for a chain that would defeat the ordering.
_MISORDERED_MIDDLEWARE_MESSAGE = (
    "GraphQLRequestBodyBoundaryMiddleware must appear BEFORE Django's CsrfViewMiddleware in "
    "MIDDLEWARE: the CSRF check reads request.POST, which parses a multipart body, so a "
    "request-body boundary listed after it can no longer run before the parse it exists to "
    "prevent."
)

#: Sentinel separating a foreign marked class with no Django setup lifecycle from
#: a class that explicitly shadows ``setup`` with a non-callable value. The former
#: retains the boundary-only recognition contract; the latter must fail exactly as
#: ``View.as_view`` would when it tries to call the existing attribute.
_NO_SETUP = object()


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
        """Publish the request this middleware is handling, then call downstream.

        The request object rather than a bare "installed" flag, because the
        question the exemption has to answer is per-request - *was the boundary
        run for this one?* - and the answer is the ``_BOUNDARY_ENFORCED`` stamp
        ``process_view`` writes on that same object. Publishing the request
        is therefore what lets one read answer the narrow question instead of the
        broad one.

        The mark spans the downstream call rather than the ``process_view`` hook
        alone, because it is read by the CSRF middleware - which may be *any*
        later entry in the chain - and reset in a ``finally`` so a raising view
        cannot leave it set for whatever the worker handles next.
        """
        if iscoroutinefunction(self):
            return self.__acall__(request)
        token = _boundary_middleware_request.set(request)
        try:
            return self.get_response(request)
        finally:
            _boundary_middleware_request.reset(token)

    async def __acall__(self, request: HttpRequest) -> Any:
        """The async twin of :meth:`__call__` - the ``await`` is the whole difference.

        Separate rather than shared because the reset has to happen after the
        downstream response exists: returning the coroutine from a synchronous
        ``finally`` would reset the mark before the CSRF middleware ever read it.
        """
        token = _boundary_middleware_request.set(request)
        try:
            return await self.get_response(request)
        finally:
            _boundary_middleware_request.reset(token)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., Any],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> HttpResponseBase | None:
        """Run a package view's body boundary here, before any later ``process_view``.

        The boundary itself is the view's, reached through an instance built and
        set up the way ``View.as_view`` builds and sets one up - and built only
        from a class :func:`_package_view_instance` has established carries that
        boundary - so the limit that applies is the mount's own
        ``max_request_body_bytes`` and this module states no policy. Running
        ``setup`` before the boundary is load-bearing: a consumer subclass may
        derive request-local boundary state there, and stamping a request after
        checking the pre-setup instance would make the real view skip that state.
        A refusal
        becomes the same ``text/plain`` response upstream's ``dispatch`` produces
        for the identical ``HTTPException``, so a client cannot tell from the
        response which side of the CSRF check refused it.

        It is invoked under the name the recognition probed for - reached through
        ``_boundary_ordering.py::_BOUNDARY_METHOD``, not spelled again here - so the
        boundary this hook runs cannot come to differ from the boundary it accepted
        the class for. A literal attribute access would state that name a second
        time, and the drift it permits is exactly the failure the probe exists to
        remove: an ``AttributeError`` out of this hook, on the one class of input the
        recognition had just vouched for.

        A callback :func:`_package_view_instance` declines is left entirely alone:
        no boundary run here, and therefore no stamp, which is what leaves that
        request on the view-local arrangement rather than on neither.
        """
        if getattr(request, _BOUNDARY_ENFORCED, False):
            return None
        view = _package_view_instance(view_func)
        if view is None:
            return None
        setup = getattr(view, "setup", _NO_SETUP)
        if setup is not _NO_SETUP:
            setup(request, *view_args, **view_kwargs)
            if not hasattr(view, "request"):
                raise AttributeError(
                    f"{type(view).__name__} instance has no 'request' attribute. "
                    "Did you override setup() and forget to call super()?",
                )
        try:
            getattr(view, _BOUNDARY_METHOD)(request)
        except HTTPException as exc:
            return HttpResponse(
                content=exc.reason,
                status=exc.status_code,
                content_type="text/plain",
            )
        try:
            mount = getattr(view_func, _BOUNDARY_MOUNT, None)
        except Exception:  # an optional handoff cannot turn a completed boundary into a 500
            mount = None
        if mount is not None:
            setattr(request, _BOUNDARY_PREPARED_VIEW, (mount, view))
        setattr(request, _BOUNDARY_ENFORCED, True)
        return None


def _package_view_instance(view_func: Callable[..., Any]) -> Any:
    """The package view instance whose boundary this callback's mount would run.

    ``None`` means "not a callback this middleware can run a boundary for", and
    that is the whole answer :meth:`GraphQLRequestBodyBoundaryMiddleware
    .process_view` branches on: a declined callback is left with the request
    unstamped, so the view supplies the ordering itself and the CSRF exemption
    stays true (``_boundary_ordering.py::_CsrfOrderingExemption``).

    The recognition is one decision and it ends at the boundary, because the
    boundary is the answer: the marker
    ``views.py::_RequestBodyBoundaryMixin.as_view`` stamps, a ``view_class`` that
    is a class, a ``view_initkwargs`` mapping - Django's own ``as_view``
    bookkeeping, and what makes the built instance carry the mount's own
    ``max_request_body_bytes`` - a ``view_class`` that itself carries the boundary
    method named by ``_boundary_ordering.py::_BOUNDARY_METHOD``, and then a
    construction that the class actually accepts those kwargs for. A wrapper can
    copy the marker with bookkeeping of any shape behind it, bookkeeping can be
    shaped exactly like ``as_view``'s while naming kwargs the class rejects, and a
    ``view_class`` can be a real, buildable class that is no package view at all,
    so a recognition that stopped short of the boundary - at the shape of the
    bookkeeping, or at the instance the bookkeeping builds - would still turn a
    foreign callback into an unhandled ``500`` from a hook whose every other
    outcome is a controlled response.

    The boundary is probed on the class rather than on the built instance because
    the boundary is exactly what :meth:`GraphQLRequestBodyBoundaryMiddleware
    .process_view` then runs, and because probing the instance would answer the
    same question one step too late, having already run a foreign class's
    ``__init__``. It is probed for a *callable* rather than for presence: an
    attribute of that name which cannot be called is not a boundary this
    middleware can run either, and recognizing it would hand ``process_view`` the
    same uncontrolled failure the probe exists to remove. The name is reached
    through ``_boundary_ordering.py``, which is what lets the probe cost no import
    of ``views.py``. One limit, stated rather than left to be discovered: an
    attribute read consults the object's own attribute machinery, so a forged
    ``view_class`` whose metaclass defines ``__getattr__``, or which carries a
    descriptor under the probed name, still runs that code. Forging the marker is
    outside the threat model either way, and the probe is here so that every
    outcome the recognition reaches is a controlled response - a refusal, a stamp,
    or a decline - not to defend against a forger. Running a boundary the
    recognition accepted is a different question: a boundary that raises anything
    but an ``HTTPException`` leaves ``process_view`` uncaught, deliberately and
    identically for a package mount and for a forged class carrying a callable of
    the probed name, because a guard there would sit across the body cap's own
    errors.

    Which is why every read the recognition performs is guarded: attribute
    machinery of that kind can raise instead of answering, ``getattr``'s default
    absorbs ``AttributeError`` alone, and ``process_view`` calls this function
    outside any ``except``, so one unguarded read would leave the hook on an
    exception of the forged object's choosing. A read that cannot be completed is
    a question that cannot be answered, and the answer to that is ``None``: the
    callback is declined and keeps the view-local arrangement, so the cap still
    runs and what degrades is the CSRF class rather than the ordering. It masks
    no misconfiguration of a *package* mount either, because a boundary read that
    genuinely raises on a package class raises again in
    ``views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once``, which
    is exactly what a declined request goes on to run.

    The ``TypeError`` arm is therefore the answer being absent rather than a
    failure being swallowed: it is raised by the splat and by the class's own
    signature, the two ways a callback can carry the bookkeeping without a
    buildable instance behind it, and both mean "not a callback whose boundary I
    can run". With the probe ahead of it, what reaches it is a class carrying a
    callable of the probed name that cannot be built from the kwargs it names: a
    package class named with kwargs it rejects, a package subclass whose own
    ``__init__`` raises, and equally a forged class whose accepted ``__init__``
    raises ``TypeError``. It hides no misconfiguration of a *package* mount,
    because Django's own ``as_view`` closure constructs the same class with the
    same kwargs for the same request, so a mount that genuinely cannot be built
    still fails there - as it would with this middleware uninstalled. It stays
    narrow for that reason while the reads above are guarded broadly: a class that
    cannot be built from the kwargs it names is a determined answer, and a read
    that raises is no answer at all. The two ``isinstance`` tests stay ahead of the
    probe and the construction, so the read is taken off a class rather than off an
    arbitrary object - which narrows whose attribute machinery can run, a class's own
    metaclass and descriptors rather than any object's ``__getattr__``, and does
    not eliminate it - and so it is only ever a class that gets called. There is
    deliberately no ``or {}`` default: an absent attribute means "not ours", never
    "ours, with nothing configured".
    """
    try:
        if not getattr(view_func, _BOUNDARY_MARKER, False):
            return None
        view_class = getattr(view_func, "view_class", None)
        initkwargs = getattr(view_func, "view_initkwargs", None)
        if not isinstance(view_class, type) or not isinstance(initkwargs, dict):
            return None
        if not callable(getattr(view_class, _BOUNDARY_METHOD, None)):
            return None
    except Exception:  # a read that cannot answer has recognized nothing
        return None
    try:
        return view_class(**initkwargs)
    except TypeError:
        return None


def _require_boundary_before_csrf() -> None:
    """Raise ``ConfigurationError`` when a CSRF entry precedes this middleware.

    Read off ``settings.MIDDLEWARE`` at instantiation - which is chain-build time,
    so a misordered deployment fails at startup rather than on the first
    multipart request. Entries are resolved and compared by class rather than by
    dotted path, so a subclass of either middleware is recognized as what it is;
    a non-class entry (a function middleware) is neither and is skipped.

    The first entry of each middleware type in ``MIDDLEWARE`` is what decides the
    comparison: the first boundary entry is what runs first to measure the body,
    and the first CSRF entry is what would parse it.

    Nothing is raised when the chain contains no CSRF middleware at all: there is
    then no read to run behind, and the package view's own CSRF continuation
    still protects the endpoint.
    """
    boundary_index = csrf_index = None
    for index, path in enumerate(settings.MIDDLEWARE):
        entry = import_string(path)
        if not isinstance(entry, type):
            continue
        if issubclass(entry, GraphQLRequestBodyBoundaryMiddleware) and boundary_index is None:
            boundary_index = index
        elif issubclass(entry, CsrfViewMiddleware) and csrf_index is None:
            csrf_index = index
    if boundary_index is None or csrf_index is None or csrf_index > boundary_index:
        return
    raise ConfigurationError(_MISORDERED_MIDDLEWARE_MESSAGE)
