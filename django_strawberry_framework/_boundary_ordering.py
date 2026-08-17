"""The marks and the method name the request-body boundary's ordering rests on.

``views.py`` owns the boundary itself - the cumulative body cap (spec-046
Decision 7) and the header-only wire-encoding refusals (Decision 9) - while
``middleware/request_body.py`` owns *where in the request lifecycle* it runs
(Decision 18). Those two modules have to agree about the boundary's completion
and prepared view per request, the identity of the mounted callback, and one
static fact concerning the view class itself. The per-request agreement runs in
both directions, so the marks, names, and their meanings live here rather than
in either of them: neither of the two imports the other, and this module imports
nothing but the standard library.

The protocol
------------

:data:`_BOUNDARY_MARKER` is stamped on the view callback by
``views.py::_RequestBodyBoundaryMixin.as_view`` and read by the boundary
middleware. It says: *this callback mounts a package view whose body boundary a
chain entry can run.* An attribute rather than a class check, so recognizing a
package callback needs no import of the view classes.

:data:`_BOUNDARY_ENFORCED` is stamped on the request by the boundary middleware
once it has run that boundary, and read by
``views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once`` and by
:class:`_CsrfOrderingExemption`. It says: *this request's body has already been
measured, by a chain participant, before anything parsed it.*

:data:`_BOUNDARY_MOUNT` identifies one callback returned by
``views.py::_RequestBodyBoundaryMixin.as_view``. When the middleware prepares
that mount's view instance through Django's normal ``setup`` lifecycle, it puts
the token and instance on the request under :data:`_BOUNDARY_PREPARED_VIEW`.
The callback consumes only an instance carrying its own token. This makes the
view whose boundary ran the view whose ``dispatch`` continues: request-derived
boundary state and lifecycle side effects cannot diverge across two instances.

:data:`_BOUNDARY_METHOD` is not a mark and not per-request: it is the *name* of
the boundary method ``views.py::_RequestBodyBoundaryMixin`` defines, read by the
boundary middleware off a marked callback's ``view_class`` before that class is
constructed, and used again to invoke that boundary on the instance it then
builds. It says: *this class is one whose boundary a chain entry can run.*
It lives here for the same reason the marks do - the middleware has to recognize
the boundary without importing the module that defines it, and a name held in the
consumer of the protocol rather than in the protocol itself is a fact stated
twice. Both of the middleware's uses read it from here, which is what makes the
name the recognition accepts a class for the same name the hook runs; spelling it
at the call site would be that second statement, and the two could then drift.

The invariant :class:`_CsrfOrderingExemption` rests on is that the stamp has one
writer: it is written only by a chain participant that has already run the
boundary for that request, so an absent stamp means the view still owns the
ordering. That is why the exemption is keyed off the stamp rather than off the
middleware being installed - "installed" is a property of the chain, "ordered" is
a property of the request, and only the second one licenses handing the CSRF
check over to the chain.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from django.http import HttpRequest


#: Stamped on the callback ``_RequestBodyBoundaryMixin.as_view`` returns, and the
#: only thing that makes a resolved view a package view as far as the boundary
#: middleware is concerned. A callback that does not carry it is not one whose
#: boundary that middleware can run, whatever else it carries.
_BOUNDARY_MARKER = "graphql_request_body_boundary"

#: Stamped on a request whose boundary a chain participant has already run, so
#: the view does not measure the same body twice - and so the CSRF exemption is
#: withdrawn for exactly the requests whose ordering the chain supplied. Read by
#: both package views at the top of ``run``.
_BOUNDARY_ENFORCED = "graphql_request_body_boundary_enforced"

#: Stamped on one package callback with an opaque per-mount token, then copied by
#: ordinary Django decorators along with the callback's other attributes.
_BOUNDARY_MOUNT = "graphql_request_body_boundary_mount"

#: Stamped on a request with ``(mount token, prepared view instance)`` after the
#: middleware has set that instance up and successfully run its boundary. The
#: matching package callback consumes it before dispatch.
_BOUNDARY_PREPARED_VIEW = "graphql_request_body_boundary_prepared_view"

#: The name of the boundary method a package view carries, probed on a marked
#: callback's ``view_class`` by the boundary middleware before it builds anything -
#: and then the name it invokes on the instance it builds, so the boundary that runs
#: is the one the probe accepted the class for.
#: Defined by ``views.py::_RequestBodyBoundaryMixin._enforce_request_boundary`` and
#: named here because the middleware has to recognize it without importing that
#: module. A class carrying no callable of this name is not one whose boundary that
#: middleware can run, whatever else it carries.
_BOUNDARY_METHOD = "_enforce_request_boundary"

#: The request the boundary middleware is currently handling, or ``None`` outside
#: any such request - the one fact :class:`_CsrfOrderingExemption` needs that the
#: view callback cannot carry, since a callback attribute is process-wide while
#: the chain a request travels through is not. A ``ContextVar`` rather than a
#: thread local so the async chain sees it too, and it is set and reset around the
#: downstream call so it can never leak into an unrelated request.
_boundary_middleware_request: ContextVar[HttpRequest | None] = ContextVar(
    "django_strawberry_framework_boundary_middleware_request",
    default=None,
)


class _CsrfOrderingExemption:
    """The package view callback's ``csrf_exempt`` value: true only when needed.

    ``CsrfViewMiddleware.process_view`` consults the mark as
    ``if getattr(callback, "csrf_exempt", False)``, so the value is read for its
    truthiness at request time - which is what lets one object answer the
    question the package actually has to answer: *has something else already run
    the body boundary for THIS request, ahead of the CSRF check?*

    Only an established yes withdraws the exemption, and establishing it takes
    both marks: the request is the one the boundary middleware is handling, and
    it carries the :data:`_BOUNDARY_ENFORCED` stamp that middleware writes after
    running the boundary. The deployment's own ``CsrfViewMiddleware`` (or
    subclass) then runs normally, after the boundary.

    Every other state answers yes to "does the view still have to supply the
    ordering itself?", which is the arrangement that predates the boundary
    middleware: the exemption is true, the chain's CSRF middleware skips the
    callback, and the view runs the boundary and re-enters CSRF from inside the
    view. A request that travelled no such chain lands there, and so does one
    whose callback the middleware did not recognize - which degrades the CSRF
    *class* to Django's stock implementation rather than degrading the
    *ordering* the body refusal depends on.

    It is never a bypass in either state: exactly one complete CSRF check runs on
    every request that gets past the boundary.
    """

    def __bool__(self) -> bool:
        """Whether the view still has to supply the ordering itself.

        Two clauses rather than one ``getattr`` on a possibly-``None`` receiver:
        "no boundary middleware is handling this request" and "one is, and it has
        not run the boundary for this request" are different facts that happen to
        want the same answer here, and folding an absence into a ``getattr``
        default is how the answer stops being readable once a third case exists.
        """
        request = _boundary_middleware_request.get()
        return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)


#: One instance, shared by every package view callback - it carries no per-view
#: state, and its answer is a property of the request rather than of the mount.
_CSRF_ORDERING_EXEMPTION = _CsrfOrderingExemption()
