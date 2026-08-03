"""Package-tier contracts for the package's Django GraphQL views (spec-046).

Deliberately narrow: this file holds only what a live request cannot express
(spec-046 Decision 13, Placement). Every request-shaped S1 proof - project
middleware, ``ALLOWED_HOSTS``, CSRF, security headers, cache policy, exact
routing, and the per-mount IDE / GET controls - is earned over fakeshop's real
``/graphql/`` in ``examples/fakeshop/test_query/test_transport_api.py``.

What stays here:

- the ``channels``-free import boundary (Decision 6 / Error shapes) - a proof
  about ABSENCE, which a live request cannot make;
- the ``as_view`` keyword surface, including the fact that Django's
  class-attribute guard is what admits or rejects a keyword (the constraint
  the cap keyword satisfies with a class attribute on the mixin);
- the async twin's coroutine marking, pinned here so it does not depend on the
  live async probe surviving;
- the body-cap knob: the ``max_request_body_bytes`` precedence ladder and
  its validation (properties of a pure function, not of a request), plus the
  enforcement branches whose subject is view-internal state a wire response
  cannot show - that an over-limit *declaration* is refused without
  ``request._body`` ever being materialized, that a multipart request stays
  unmaterialized, that GET is a no-op, and above all *how* the body is measured:
  a wire ``413`` is identical whether the rejection cost one ``seek`` or a
  full-body allocation, so the bound itself is only assertable from here. Every
  request-shaped cap row (status codes, the reason on the wire, the parse /
  execution witnesses, the ASGI fragment shapes) is live in
  ``examples/fakeshop/test_query/test_transport_api.py``;
- the strict UTF-8 wire contract, now that the package view owns it
  (spec-046 Decision 9): the per-encoding ``__cause__`` matrix, which is
  invisible over the wire because all nine rejected shapes carry the identical
  status and message by design.

The schema is module-local and ORM-free: none of these contracts touches the
database, so no ``django_db`` marker and no registry mutation.
"""

import contextlib
import importlib
import io
import json
import logging
import sys
import tempfile
from io import BytesIO
from unittest import mock

import pytest
import strawberry
from asgiref.sync import iscoroutinefunction
from cross_web import (
    AsyncDjangoHTTPRequestAdapter,
    DjangoHTTPRequestAdapter,
    HTTPException,
)
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    RawPostDataException,
    UnreadablePostError,
)
from django.middleware.csrf import CsrfViewMiddleware
from django.test import (
    AsyncClient,
    AsyncRequestFactory,
    Client,
    RequestFactory,
    override_settings,
)
from django.urls import path
from strawberry.django.views import AsyncGraphQLView, GraphQLView
from strawberry.http.base import BaseView

import django_strawberry_framework
from django_strawberry_framework import _cross_web_patches as cross_web_patches
from django_strawberry_framework import _strawberry_patches as patches
from django_strawberry_framework._request_body import (
    _CORRUPTED_PROBE_LOG_MESSAGE,
    _UNREADABLE_STREAM_LOG_MESSAGE,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.middleware.request_body import (
    _BOUNDARY_ENFORCED,
    _BOUNDARY_MARKER,
    GraphQLRequestBodyBoundaryMiddleware,
)
from django_strawberry_framework.views import (
    _BODY_LIMIT_REASON,
    _JSON_PARSE_REASON,
    AsyncDjangoGraphQLView,
    DjangoGraphQLView,
    _declared_content_length,
    _RawBodyRequestAdapter,
    _resolved_max_request_body_bytes,
)
from tests._soft_dependency import evicted_modules, simulated_absence

# Captured at import so the ``channels``-absence test can compare UPSTREAM's own
# class objects across the simulated absence. Comparing the package view's
# ``__base__`` would silently stop proving anything the moment the base list
# changes (which the body-cap mixin did); upstream's class identity is the thing
# the assertion is actually about.
_UPSTREAM_VIEWS = (GraphQLView, AsyncGraphQLView)

# ``"channels"`` is the sentinel name and heads the prefix list inside the
# helper, so it is NOT repeated here; ``django_strawberry_framework.views`` is
# evicted so the import under test genuinely re-executes the module body.
# ``strawberry.django`` is evicted too - but through its OWN two-sided guard, see
# the absence test - so the ONE upstream module ``views.py`` imports re-executes
# under the sentinel instead of answering from the module cache.
_ABSENCE_PREFIXES = ("strawberry.channels", "daphne", "django_strawberry_framework.views")

_VIEW_CLASSES = (
    pytest.param(DjangoGraphQLView, id="sync"),
    pytest.param(AsyncDjangoGraphQLView, id="async"),
)


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"


SCHEMA = strawberry.Schema(query=Query)


def test_views_module_imports_with_channels_absent():
    """The HTTP half of the card needs no ``channels`` - the documented asymmetry.

    ``routers.py`` raises its install hint the moment a consumer reaches for the
    router symbol; ``views.py`` must not, because a WSGI-only project adopts the
    GraphQL view without ever installing the soft dependency (Decision 6 / Error
    shapes).

    What this proves, exactly: ``views.py``'s own body AND the body of the
    upstream module it imports (``strawberry.django.views``, plus that package's
    ``__init__`` and ``context``) re-execute while ``sys.modules["channels"]`` is
    the ``None`` sentinel, so any ``channels``-reaching import on either would
    raise ``ImportError`` here. The identity assertions are what make that
    load-bearing rather than decorative: a re-executed module body produces NEW
    class objects, so ``is not`` against the module-scope imports is direct
    evidence the bodies really ran under the sentinel instead of answering from
    the module cache. Modules already imported BELOW that boundary
    (``strawberry.http``, ``cross_web``, ``django``, and the package's own
    ``conf`` / ``exceptions``) stay cached; the first three are upstream's own
    contract and the last two are proven ``channels``-free by inspection - their
    whole import surface is ``django.conf`` / ``django.test.signals`` and the
    standard library.

    Upstream's side is pinned by UPSTREAM's own class identity rather than by the
    package view's ``__base__``: ``_RequestBodyBoundaryMixin`` sits first in
    the bases, so a ``__base__`` comparison would now compare the PACKAGE's mixin
    to itself and pass while proving nothing about upstream. Asserting the fresh
    upstream class ``is not`` the captured one AND appears in the fresh package
    view's ``__mro__`` is strictly stronger and independent of the base list.

    ``strawberry.django`` gets its own ``evicted_modules`` guard rather than a bare
    entry in ``_ABSENCE_PREFIXES``: re-executing a third-party package body rebinds
    ``django`` on the ``strawberry`` package object, and only the ``(parent, attr)``
    two-sided restore puts the attribute path and the import path back on ONE
    module object afterwards (spec-041 D3, the divergence ``evicted_modules``
    exists to prevent). Composing the helper twice is the file-local idiom for
    that; no new eviction machinery.
    """
    with (
        evicted_modules("strawberry.django", parent=strawberry, attr="django"),
        simulated_absence(
            "channels",
            *_ABSENCE_PREFIXES,
            parent=django_strawberry_framework,
            attr="views",
        ),
    ):
        assert sys.modules["channels"] is None
        # Preconditions: both bodies really are out of the cache.
        assert "django_strawberry_framework.views" not in sys.modules
        assert "strawberry.django.views" not in sys.modules

        module = importlib.import_module("django_strawberry_framework.views")

        assert isinstance(module.DjangoGraphQLView, type)
        assert isinstance(module.AsyncDjangoGraphQLView, type)
        assert "strawberry.channels" not in sys.modules
        # Fresh class objects on both sides of the boundary: the package's body
        # ran, and so did upstream's.
        assert module.DjangoGraphQLView is not DjangoGraphQLView
        assert module.AsyncDjangoGraphQLView is not AsyncDjangoGraphQLView

        upstream = importlib.import_module("strawberry.django.views")
        fresh_upstream = (upstream.GraphQLView, upstream.AsyncGraphQLView)
        fresh_package = (module.DjangoGraphQLView, module.AsyncDjangoGraphQLView)
        for captured, fresh, package_view in zip(
            _UPSTREAM_VIEWS,
            fresh_upstream,
            fresh_package,
            strict=True,
        ):
            assert fresh is not captured
            assert fresh in package_view.__mro__
            assert captured not in package_view.__mro__


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_every_upstream_as_view_kwarg_still_binds_on_the_package_views(view_class):
    """Every upstream ``as_view()`` keyword keeps working, unchanged (Decision 6).

    All four are declared class attributes upstream (``schema``,
    ``graphql_ide``, ``allow_queries_via_get`` on the Django views;
    ``multipart_uploads_enabled`` on ``strawberry.http.base.BaseView``), so
    Django binds them and stashes them on ``view_initkwargs`` for the
    per-request instantiation. The subclass adds nothing and takes nothing away.
    """
    view = view_class.as_view(
        schema=SCHEMA,
        graphql_ide=None,
        allow_queries_via_get=False,
        multipart_uploads_enabled=True,
    )

    assert view.view_class is view_class
    assert view.view_initkwargs == {
        "schema": SCHEMA,
        "graphql_ide": None,
        "allow_queries_via_get": False,
        "multipart_uploads_enabled": True,
    }


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_an_unknown_as_view_kwarg_is_rejected_by_djangos_class_attribute_guard(view_class):
    """Django's ``View.as_view`` admits only keywords that are already class attributes.

    The consequence a later slice depends on: a view keyword the package wants to
    accept (the S2 body cap's per-mount override) has to be declared as a CLASS
    attribute on the package view, not merely handled in ``__init__``. The bogus
    keyword here is deliberately unrelated to any planned one so this test never
    has to change when that lands.
    """
    with pytest.raises(TypeError, match="invalid keyword"):
        view_class.as_view(schema=SCHEMA, not_a_view_kwarg=1)


def test_async_view_as_view_is_marked_as_a_coroutine_function():
    """The async twin's ``as_view()`` result is a coroutine function; the sync one is not.

    Upstream's ``AsyncGraphQLView.as_view`` calls ``markcoroutinefunction`` on the
    view it returns - Django would otherwise report ``view_is_async`` as ``False``
    (neither view defines ``get`` / ``post`` handlers) and dispatch the async view
    on an executor thread. A subclass inherits that unchanged; this pins it.
    """
    assert iscoroutinefunction(AsyncDjangoGraphQLView.as_view(schema=SCHEMA)) is True
    assert iscoroutinefunction(DjangoGraphQLView.as_view(schema=SCHEMA)) is False


def test_module_exports_exactly_the_two_view_classes_and_stays_off_the_package_root():
    """A leaf-module import, never a package-root export (Decision 6).

    Matches the posture of every other integration surface (``routers.py``,
    ``middleware/debug_toolbar.py``, ``extensions/``): the consumer imports from
    ``django_strawberry_framework.views``, and neither the module name nor either
    class appears on the root ``__all__``.
    """
    from django_strawberry_framework import views as views_module

    assert views_module.__all__ == ("AsyncDjangoGraphQLView", "DjangoGraphQLView")
    root_surface = django_strawberry_framework.__all__
    assert "views" not in root_surface
    assert "DjangoGraphQLView" not in root_surface
    assert "AsyncDjangoGraphQLView" not in root_surface


# ---------------------------------------------------------------------------
# The body cap's knob. The pure-function precedence + validation
# matrices, the keyword's binding through ``as_view``, and the three
# enforcement branches whose witness is view-internal state.
# ---------------------------------------------------------------------------


def _settings_with(value):
    """Override only ``MAX_REQUEST_BODY_BYTES``, leaving the rest of the dict absent."""
    return override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"MAX_REQUEST_BODY_BYTES": value})


@pytest.mark.parametrize(
    ("kwarg", "setting", "expected"),
    [
        pytest.param(512, None, 512, id="kwarg-beats-setting-none"),
        pytest.param(512, 4096, 512, id="kwarg-beats-setting-int"),
        pytest.param(None, 4096, 4096, id="setting-when-no-kwarg"),
        pytest.param(None, None, None, id="setting-none-disables"),
    ],
)
def test_the_cap_precedence_ladder_is_kwarg_then_setting_then_default(kwarg, setting, expected):
    """``max_request_body_bytes=`` > ``MAX_REQUEST_BODY_BYTES`` > the default.

    The two ``None``s mean different things by design (spec-046 Decision 7 step
    4): a ``None`` KWARG says "this mount did not override anything" and defers,
    while ``None`` IN THE SETTING is the documented way to disable the package
    cap. Both rungs are exercised here against an explicitly-set setting so no
    row depends on ambient project settings.
    """
    with _settings_with(setting):
        assert _resolved_max_request_body_bytes(kwarg) == expected


def test_no_kwarg_and_no_setting_resolves_to_the_one_megabyte_default():
    """The default is applied ONCE, by ``conf.py``'s accessor - not restated in ``views.py``.

    Asserted against an entirely empty settings dict (the key absent rather than
    ``None``, which would mean "disabled"), so this pins the accessor default
    reaching the resolver rather than a literal duplicated in the view module.
    """
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={}):
        assert _resolved_max_request_body_bytes(None) == 1_048_576


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
        pytest.param(True, id="bool-true"),
        pytest.param("4096", id="str"),
        pytest.param(4096.0, id="float"),
        pytest.param(object(), id="object"),
    ],
)
@pytest.mark.parametrize("rung", ["kwarg", "setting"])
def test_an_invalid_cap_value_raises_configuration_error_on_either_rung(bad, rung):
    """Both precedence rungs are validated, and the message points at the fix.

    ``0`` is rejected rather than read as "unlimited": it is the near-universal
    unlimited spelling elsewhere, but under this cap's ``>`` comparison it would
    mean "reject every non-empty body", so a loud failure is the only reading
    that cannot be misread. ``True`` is rejected because the gate admits the
    built-in ``int`` exactly - ``bool`` is a subclass, so an ``isinstance`` gate
    would have let it through - and a boolean cap is always a mistake.
    The message must name the received type AND ``None`` as the documented
    disable, or a consumer who hits it cannot tell which value to reach for.
    """
    expected_type = type(bad).__name__
    with pytest.raises(ConfigurationError, match=rf"None to disable.*got {expected_type}\b"):
        if rung == "kwarg":
            with _settings_with(4096):
                _resolved_max_request_body_bytes(bad)
        else:
            with _settings_with(bad):
                _resolved_max_request_body_bytes(None)


@pytest.mark.parametrize("rung", ["kwarg", "setting"])
def test_a_cap_value_too_large_to_render_still_raises_configuration_error(rung):
    """An unrenderable rejected value must not replace the typed error.

    A separate row from the matrix above on purpose: that one proves the message
    NAMES the received type, while this one proves the message cannot itself
    fail. CPython 3.11+ refuses to convert an integer with more than
    ``sys.get_int_max_str_digits()`` digits to a string, and the ``got``
    tail is built by an f-string at the RAISE SITE - before any exception object
    exists - so ``DjangoStrawberryFrameworkError``'s own ``__str__`` guard cannot
    intercept it. Interpolating ``{value!r}`` directly therefore raised
    ``ValueError`` instead of ``ConfigurationError`` on exactly the
    hostile-configuration path where the typed error is the contract; the tail is
    rendered by ``exceptions.py::describe_value`` so it degrades to a
    type-naming placeholder instead. The negative value is what reaches the
    ``value <= 0`` arm.
    """
    bad = -(10**10000)
    with pytest.raises(ConfigurationError, match=r"None to disable.*got an unprintable int"):
        if rung == "kwarg":
            with _settings_with(4096):
                _resolved_max_request_body_bytes(bad)
        else:
            with _settings_with(bad):
                _resolved_max_request_body_bytes(None)


class _HostileInt(int):
    """An ``int`` whose ordering raises - the comparison dunder is overridable."""

    def __le__(self, other):
        raise RuntimeError("hostile comparison")


class _WellBehavedInt(int):
    """An ``int`` subclass that behaves perfectly and is still not an ``int``."""


@pytest.mark.parametrize(
    "subclass_value",
    [
        pytest.param(_HostileInt(4096), id="int-subclass-whose-comparison-raises"),
        pytest.param(_WellBehavedInt(4096), id="well-behaved-int-subclass"),
    ],
)
@pytest.mark.parametrize("rung", ["kwarg", "setting"])
def test_the_cap_admits_the_builtin_int_exactly(subclass_value, rung):
    """The cap's type gate is exact: a subclass of ``int`` is not an ``int``.

    A subclass may override ``__le__``, so admitting one would run consumer code
    inside the resolver and let a raw exception replace the typed
    ``ConfigurationError`` the boundary promises. The well-behaved row states the
    resulting contract without hedging: the rejection is about the TYPE, not
    about whether a particular instance happens to misbehave, because only the
    type is knowable before the comparison runs. Both precedence rungs are
    covered because either can carry the value.
    """
    with pytest.raises(ConfigurationError, match="None to disable"):
        if rung == "kwarg":
            with _settings_with(4096):
                _resolved_max_request_body_bytes(subclass_value)
        else:
            with _settings_with(subclass_value):
                _resolved_max_request_body_bytes(None)


@pytest.mark.parametrize(
    ("content_length", "expected"),
    [
        pytest.param("4096", 4096, id="parseable"),
        pytest.param(None, None, id="absent"),
        pytest.param("not-a-number", None, id="unparseable"),
        pytest.param("", None, id="empty"),
    ],
)
def test_the_declared_length_reader_is_none_for_every_unmeasurable_shape(content_length, expected):
    """An absent or garbage ``CONTENT_LENGTH`` reads as ``None``, never as a number.

    ``None`` is the fail-safe direction: an unmeasurable declaration falls
    through to the counted check rather than being trusted, so a hostile client
    cannot buy a larger body by omitting or corrupting the header. ``int(None)``
    raises ``TypeError`` and ``int("not-a-number")`` raises ``ValueError``, which
    is why the helper catches both rather than only one.
    """
    request = RequestFactory().post("/graphql/", data=b"x" * 16, content_type="application/json")
    if content_length is None:
        del request.META["CONTENT_LENGTH"]
    else:
        request.META["CONTENT_LENGTH"] = content_length

    assert _declared_content_length(request) == expected


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_the_cap_keyword_binds_through_as_view_on_both_classes(view_class):
    """``max_request_body_bytes=`` is admitted by Django's class-attribute guard.

    The companion to the rejected-bogus-keyword test above: Django's
    ``View.as_view`` uses ``hasattr``, so declaring the attribute on
    ``_RequestBodyBoundaryMixin`` (rather than on each view, or only handling it in
    ``__init__``) is what makes the keyword bindable on both classes. Pinning
    ``view_initkwargs`` proves it reaches the per-request instantiation rather
    than being silently dropped, and the class-attribute default pins that a
    mount which omits the keyword defers to the setting.
    """
    assert view_class.max_request_body_bytes is None

    view = view_class.as_view(schema=SCHEMA, max_request_body_bytes=4096)

    assert view.view_initkwargs == {"schema": SCHEMA, "max_request_body_bytes": 4096}


def _capped_view(limit, view_class=DjangoGraphQLView):
    """A package view instance with the cap set, built the way ``as_view`` builds one.

    ``as_view`` instantiates with ``cls(**initkwargs)``, and Django's
    ``View.__init__`` ``setattr``s every keyword, so this is the same instance
    shape a real mount produces - reached directly because these rows' subject is
    ``_enforce_request_body_limit`` against a ``RequestFactory`` request, not the
    dispatch path the live tier owns.
    """
    return view_class(schema=SCHEMA, max_request_body_bytes=limit)


def test_a_declared_over_limit_request_is_refused_without_touching_the_stream():
    """Decision 7 step 1: the declared gate rejects before the body is even measured.

    The untouched stream is the load-bearing half. A ``413`` alone would be
    satisfied by an implementation that read and measured the whole payload first;
    the point of the declared gate is that an honestly-declared oversized request
    costs nothing at all to refuse. The under-limit control in the same test is
    what makes the negative witness meaningful: on WSGI the stream is a
    non-seekable ``LimitedStream``, so a measurement that had to happen shows up as
    the substituted rewound ``BytesIO`` - present on the control, absent here.
    """
    view = _capped_view(32)
    over = RequestFactory().post("/graphql/", data=b"x" * 4096, content_type="application/json")
    over_stream = over._stream

    with pytest.raises(HTTPException) as excinfo:
        view._enforce_request_body_limit(over)

    assert excinfo.value.status_code == 413
    assert excinfo.value.reason == _BODY_LIMIT_REASON
    assert hasattr(over, "_body") is False
    assert over._stream is over_stream

    under = RequestFactory().post("/graphql/", data=b"x" * 16, content_type="application/json")
    under_stream = under._stream
    view._enforce_request_body_limit(under)
    assert under._stream is not under_stream
    assert under.body == b"x" * 16


def test_a_multipart_request_under_the_declared_gate_is_never_materialized():
    """Decision 7 step 3: multipart gets the declared gate and nothing else.

    Reading ``request.body`` here would pull the whole payload into memory and
    defeat Django's streaming upload handlers, breaking the ``Upload``-scalar
    path the package ships - so the witness is that ``_body`` stays absent even
    after Django's own ``MultiPartParser`` has run and produced ``POST``. The
    declared gate still applies to multipart, which the second half asserts.
    """
    view = _capped_view(10_000)
    request = RequestFactory().post("/graphql/", data={"operations": "{}"})

    assert request.content_type == "multipart/form-data"
    view._enforce_request_body_limit(request)

    assert hasattr(request, "_body") is False
    assert request.POST["operations"] == "{}"
    assert hasattr(request, "_body") is False

    view.max_request_body_bytes = 8
    with pytest.raises(HTTPException, match="request-body limit"):
        view._enforce_request_body_limit(
            RequestFactory().post("/graphql/", data={"operations": "{}"}),
        )


def test_the_cap_is_a_no_op_on_get_even_with_a_hostile_content_length():
    """GET carries no body the view reads, so the cap does not run (Edge cases).

    A hostile ``CONTENT_LENGTH`` on a GET must not turn the IDE or a GET query
    into a ``413``: the declared gate would otherwise fire on a header that
    describes nothing. The ``variables`` / ``extensions`` query-param size is a
    separate concern, already shielded by
    ``_patched_parse_query_params``.
    """
    view = _capped_view(32)
    request = RequestFactory().get("/graphql/", CONTENT_LENGTH="999999")

    view._enforce_request_body_limit(request)

    assert hasattr(request, "_body") is False


def test_the_counted_check_fires_when_no_content_length_is_declared_at_all():
    """Decision 7 step 2: with no declaration, the REAL length decides.

    The package-tier colour of the ASGI live rows - an undeclared body is the
    shape Django's declared-length guard cannot see, and the counted check is
    the only application-level bound on it (the only one at all on the Django
    5.2 floor, whose ``HttpRequest.body`` has no seekable actual-size check).
    ``>`` not ``>=``: a body exactly AT the limit is allowed, which the third
    direction pins.
    """
    view = _capped_view(16)

    def undeclared(size):
        request = RequestFactory().post(
            "/graphql/",
            data=b"x" * size,
            content_type="application/json",
        )
        del request.META["CONTENT_LENGTH"]
        return request

    with pytest.raises(HTTPException, match="request-body limit"):
        view._enforce_request_body_limit(undeclared(17))

    view._enforce_request_body_limit(undeclared(16))
    view._enforce_request_body_limit(undeclared(1))


def test_a_disabled_cap_skips_the_check_entirely():
    """``MAX_REQUEST_BODY_BYTES = None`` leaves the body untouched by the view.

    The witness is again ``_body``: "disabled" must mean the view never measures,
    not that it measures against infinity, so a disabled mount imposes no read
    the request would not otherwise have taken.
    """
    view = _capped_view(None)
    request = RequestFactory().post("/graphql/", data=b"x" * 4096, content_type="application/json")

    with _settings_with(None):
        view._enforce_request_body_limit(request)

    assert hasattr(request, "_body") is False


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_misconfigured_mount_fails_loud_on_every_request_including_get(view_class):
    """Resolution happens FIRST, so a bad value cannot hide behind a bodyless request.

    If the GET no-op were checked before the resolve, a mount configured with a
    nonsense cap would serve the IDE happily and only fail once someone posted an
    operation. Failing on the GET too is what makes the misconfiguration a
    deployment-time error rather than a latent one.
    """
    view = _capped_view(0, view_class=view_class)

    with pytest.raises(ConfigurationError, match="positive int"):
        view._enforce_request_body_limit(RequestFactory().get("/graphql/"))


def test_the_body_boundary_mixin_stays_private_and_sits_first_in_both_base_lists():
    """The mixin is private, unexported, and ahead of upstream in the MRO.

    Privacy is proven once, by the exact-``__all__`` assertion in
    ``test_module_exports_exactly_the_two_view_classes_and_stays_off_the_package_root``;
    a second
    "the private name is absent from a two-element tuple that names neither"
    assertion here would be trivially true and would not fail for a real
    regression.

    Ordering is load-bearing rather than stylistic: the mixin's ``run`` overrides
    live on the view classes themselves, but the class attribute, the shared
    enforcement method, and ``parse_json`` must resolve to the package's
    implementation rather than to anything upstream might later define under the
    same names. Being first is also what lets a consumer subclass override any
    part.
    """
    from django_strawberry_framework import views as views_module

    mixin = views_module._RequestBodyBoundaryMixin

    assert DjangoGraphQLView.__bases__ == (mixin, GraphQLView)
    assert AsyncDjangoGraphQLView.__bases__ == (mixin, AsyncGraphQLView)
    assert DjangoGraphQLView.__mro__.index(mixin) < DjangoGraphQLView.__mro__.index(GraphQLView)


# ---------------------------------------------------------------------------
# HOW the body is measured. A wire ``413`` cannot tell a
# rejection that cost one ``seek`` from one that first copied the whole payload
# into memory, so every row below is about the operation the cap performs, not
# about the status it produces. ``_request_body.py`` owns the private-Django
# interaction these rows exercise.
# ---------------------------------------------------------------------------

#: Small enough that a hand-sized payload crosses it, so no row needs a large
#: body to be over the limit.
_PROBE_CAP = 256

#: Every byte value there is, which makes it two things at once. "Byte-for-byte
#: unchanged" is only a meaningful claim against bytes a stray decode /
#: re-encode cycle or a text-mode round trip would corrupt, and this carries a
#: NUL, a lone ``0x80``, and a ``0xFF``; and being *exactly* ``_PROBE_CAP``
#: bytes long it also pins the comparison as ``>`` rather than ``>=`` on both
#: measuring branches - a body at the limit is a legal body. It is deliberately
#: not valid JSON and is never parsed: these rows stop at ``request.body``.
_UNDER_LIMIT_BODY = bytes(range(256))


class _UnreadableSpool(tempfile.SpooledTemporaryFile):
    """A real ASGI body file whose ``read`` refuses to run.

    ``ASGIHandler.read_body`` hands Django a ``tempfile.SpooledTemporaryFile``;
    this IS that class, with the one method the cap must never reach replaced by
    an assertion. Subclassing rather than faking is what makes the rows below
    statements about the production stream: ``seek`` / ``tell`` behave exactly as
    they do in production, and the absence of ``seekable`` on Python 3.10 versus
    its presence from 3.11 is inherited rather than simulated - so the size probe
    is exercised through whichever of its two capability paths the running
    interpreter actually takes.
    """

    def read(self, *args, **kwargs):
        raise AssertionError("the cap read a stream it was supposed to size-probe")


class _RecordingNonSeekableStream:
    """A non-seekable byte source that records every read performed on it.

    The shape WSGI really presents: Django's ``LimitedStream`` subclasses
    ``io.IOBase``, so it declares ``seekable()`` -> ``False`` and raises from
    ``tell()``, and ``django.test.AsyncClient`` wraps its body the same way. Such
    a stream can only be measured by reading it, so the bound has to be asserted
    on the reads themselves - which is what ``requested`` (the size of every
    ``read`` call) and ``delivered`` (the running total handed over) record.
    """

    def __init__(self, raw):
        self._buffer = BytesIO(raw)
        self.requested = []
        self.delivered = 0
        self.closed = False

    def seekable(self):
        return False

    def read(self, size=-1):
        self.requested.append(size)
        chunk = self._buffer.read(size)
        self.delivered += len(chunk)
        return chunk

    def close(self):
        self.closed = True

    @property
    def unread(self):
        """Bytes still sitting in the stream - non-zero proves the cap stopped early."""
        return len(self._buffer.getvalue()) - self._buffer.tell()


class _UndeclaredSeekableStream(_RecordingNonSeekableStream):
    """Seekable in fact, silent about it - the Python 3.10 ``SpooledTemporaryFile``.

    ``tempfile.SpooledTemporaryFile`` only became an ``io.IOBase`` subclass in
    3.11, so at the supported 3.10 floor the ASGI body file has **no**
    ``seekable`` method at all while ``seek`` / ``tell`` work normally (verified:
    ``hasattr(spool, "seekable")`` is ``False`` at 3.10.19, ``True`` at 3.14.2).
    Reproducing that shape keeps the floor's behavior asserted from whichever
    interpreter runs the suite: the probe must fall back to ``tell()`` rather than
    give up, or the ASGI no-read guarantee silently evaporates at the exact
    version this card protects. ``read`` is inherited from the recorder and would
    register if it ran.
    """

    seekable = None

    def tell(self):
        return self._buffer.tell()

    def seek(self, offset, whence=io.SEEK_SET):
        return self._buffer.seek(offset, whence)


class _UnmeasurableStream(_RecordingNonSeekableStream):
    """Neither declares seekability nor can report its position.

    A raw, unwrapped WSGI ``wsgi.input`` pipe: no ``seekable`` method, and a
    ``tell()`` that raises ``io.UnsupportedOperation`` - which is an ``OSError``
    and a ``ValueError`` at once. The fail-safe direction is the bounded read,
    never "unmeasurable means empty".
    """

    seekable = None

    def tell(self):
        raise io.UnsupportedOperation("tell")


class _MisreportingSizeStream(_UndeclaredSeekableStream):
    """Answers a size probe with "nothing left" while every byte is still unread.

    A stream that can report a position but cannot take one: ``seek`` returns
    the offset it was handed instead of the position it reached, and never
    moves. That is what a queue- or iterator-backed custom ASGI body stream
    looks like, and it reaches the probe through the ``tell()`` capability
    fallback (no ``seekable`` method - the Python 3.10 spool shape), which is
    the path that exists at the supported floor. ``seek(0, SEEK_END)``
    therefore answers ``0``, so the probe computes a remaining count of zero
    for a full body.
    """

    def seek(self, offset, whence=io.SEEK_SET):
        return offset


class _OverReportingPositionStream(_UndeclaredSeekableStream):
    """Reports a position past its own end - the other incoherent direction.

    A wrapper that answers ``tell()`` in the coordinates of the whole HTTP
    message rather than of the body it exposes reports a position beyond that
    body's end, so ``seek(0, SEEK_END) - tell()`` comes out negative. ``seek``
    is the honest inherited one, which is the point: the lie is the position,
    and a position is the one thing a probe has to take on trust.
    """

    def tell(self):
        return super().tell() + _PROBE_CAP * 64


class _CapabilityQueryRaisingStream(_UndeclaredSeekableStream):
    """``seekable()`` itself raises - the first probe-failure stand-in.

    A wrapper that answers the capability question with an error rather than a
    boolean, which is a shape a consumer middleware or a custom ASGI server can
    present and which the previous implementation called unguarded, turning the
    request into an unrelated ``500``. Nothing has been moved when this raises, so
    the safe classification is "unmeasurable, position intact" and the bounded
    read is both available and correct.
    """

    def seekable(self):
        raise OSError("this stream refuses to answer capability queries")


class _UnseekableToEndStream(_UndeclaredSeekableStream):
    """Reports its position, then refuses the seek to the end.

    The second probe-failure stand-in. The end seek is the first call that can move
    the stream, so its failure leaves the position UNKNOWN rather than known - the
    restore has to run anyway, and only a restore that verifies may license the
    bounded read.
    """

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_END:
            raise OSError("this stream cannot seek to its end")
        return self._buffer.seek(offset, whence)


class _UnnumberedSeekStream(_UndeclaredSeekableStream):
    """A ``seek`` that returns ``None`` instead of a position, and never moves.

    The third probe-failure stand-in: the *end* this seek reports is not a position
    at all, so there is no measurement to make and none is attempted. ``seek``
    returning ``None`` is legal for a file-like object that simply does not report
    positions, and because it also does not move, the position is provably intact
    and the bounded read is the answer.
    """

    def seek(self, offset, whence=io.SEEK_SET):
        return None


class _ArithmeticRaisingPosition(int):
    """An ``int`` whose subtraction raises something no ``TypeError`` guard catches.

    A stream is free to report positions as objects of its own, and a wrapper that
    tracks offsets in some richer type is the ordinary way that happens. The
    package must therefore never execute a foreign numeric protocol inside the size
    boundary: ``RuntimeError`` here stands for every exception a ``__sub__`` may
    raise, and an ``int`` subclass is the shape that gets *past* a numeric check
    written as ``isinstance``.
    """

    def __sub__(self, other):
        raise RuntimeError("this position refuses to be subtracted")


class _ComparisonRaisingPosition(int):
    """An ``int`` whose ordering comparison raises - the second escape route.

    Even with the subtraction survived, the probe still compares its result against
    zero, and a subclass may override ``__le__`` alone. Two hostile operators
    therefore need two rows, or "the arithmetic is guarded" would be a claim about
    one expression rather than about the boundary.
    """

    def __le__(self, other):
        raise RuntimeError("this position refuses to be compared")


class _ArithmeticRaisingPositionStream(_UndeclaredSeekableStream):
    """Answers the end-seek with a position whose subtraction raises.

    Honest in every other respect: it really seeks, so the restore verifies and the
    bounded read that follows starts where the request started.
    """

    def seek(self, offset, whence=io.SEEK_SET):
        moved = self._buffer.seek(offset, whence)
        if whence == io.SEEK_END:
            return _ArithmeticRaisingPosition(moved)
        return moved


class _ComparisonRaisingPositionStream(_ArithmeticRaisingPositionStream):
    """Answers the end-seek with a position whose comparison raises instead."""

    def seek(self, offset, whence=io.SEEK_SET):
        moved = self._buffer.seek(offset, whence)
        if whence == io.SEEK_END:
            return _ComparisonRaisingPosition(moved)
        return moved


class _UnrestorableStream(_UndeclaredSeekableStream):
    """Seeks to the end and then cannot get back - the fourth probe-failure stand-in.

    The one shape that must NOT reach the bounded read: the probe has moved the
    stream to its end and the restore failed, so a read would return the tail of
    the body (here, nothing at all) rather than the request. Falling through would
    hand Strawberry a body the client never sent; the package refuses the request
    instead.
    """

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_END:
            return self._buffer.seek(offset, whence)
        raise OSError("this stream cannot seek back")


class _ReadRaisingStream(_RecordingNonSeekableStream):
    """A non-seekable request stream whose ``read`` fails before delivering anything.

    The aborted client at the earliest possible moment. ``OSError`` is what a
    socket that went away actually raises, and what
    ``django/http/request.py::HttpRequest.read`` re-raises as
    ``UnreadablePostError`` - so this reaches the cap through Django's own
    translation rather than around it, which is the point: the package's boundary
    has to be total against the exception Django produces, not against a
    hand-rolled one.
    """

    def read(self, size=-1):
        self.requested.append(size)
        raise OSError("this stream cannot be read")


class _ReadRaisingAfterPrefixStream(_RecordingNonSeekableStream):
    """Delivers one short chunk, then fails - the client that hung up mid-upload.

    The harder half, because the loop is already holding bytes when the failure
    arrives: the collected prefix must not become the request's body and the loop
    must not go back for more. The chunk is deliberately smaller than the cap, so
    the failure lands INSIDE the bounded loop rather than after it has already
    satisfied its own ``limit + 1`` bound and stopped.
    """

    def read(self, size=-1):
        self.requested.append(size)
        if len(self.requested) > 1:
            raise OSError("this stream stopped part way")
        chunk = self._buffer.read(min(size, _PROBE_CAP // 4))
        self.delivered += len(chunk)
        return chunk


@contextlib.contextmanager
def _spooled(raw, *, spool_class=_UnreadableSpool, max_size=1 << 20):
    """A rewound ``SpooledTemporaryFile`` holding ``raw``, closed on the way out.

    ``max_size=0`` forces the rollover-to-disk case, which is the shape that makes
    the unbounded read expensive rather than merely wasteful: past
    ``FILE_UPLOAD_MAX_MEMORY_SIZE`` Django's ASGI handler has already written the
    payload to disk, so ``request.body`` reads it back off the filesystem -
    synchronously, on the event loop, for the async view. Closing in a ``finally``
    keeps a rolled-over temporary file from tripping the suite's
    ``-W error`` ``ResourceWarning``.
    """
    stream = spool_class(max_size=max_size, mode="w+b")
    try:
        stream.write(raw)
        stream.seek(0)
        yield stream
    finally:
        stream.close()


def _asgi_request(stream, content_length):
    """A real ``ASGIRequest`` whose body file is ``stream``.

    ``AsyncRequestFactory`` builds the genuine ``ASGIRequest`` (``_read_started``
    already ``False``, ``META`` populated the way the ASGI handler populates it)
    but wraps its payload in a ``LimitedStream``, which is a test-client artifact
    rather than production shape. Replacing ``_stream`` with a spooled file moves
    the request *closer* to production, not further from it: that is exactly what
    ``ASGIHandler.create_request`` assigns.

    The ``content_type=`` argument is what makes the factory treat the payload as
    a raw body at all (the default is ``MULTIPART_CONTENT``, which would try to
    encode ``data`` as a form dict), but it does NOT reach ``META`` here:
    ``RequestFactory.generic`` populates ``CONTENT_TYPE``, ``CONTENT_LENGTH`` and
    ``wsgi.input`` only ``if data``, and the payload is empty. Measured: ``META``
    carries neither key and ``request.content_type`` is ``""``. Both headers are
    therefore installed explicitly, and the two asserts keep that a statement
    about the factory rather than an assumption about it:

    * ``application/json`` always, because it is the content type the cap's
      multipart carve-out must NOT match, and running these rows through an empty
      content type would exercise a shape no GraphQL client sends. The carve-out
      itself is exercised with a real ``multipart/form-data`` request in
      ``test_a_multipart_request_under_the_declared_gate_is_never_materialized``.
    * no ``Content-Length`` by default - the chunked-transfer shape, which is
      exactly the declaration the gate structurally cannot see. ``content_length``
      installs one when a row wants to understate it instead.
    """
    request = AsyncRequestFactory().post(
        "/graphql/",
        data=b"",
        content_type="application/json",
    )
    request._stream = stream
    assert "CONTENT_LENGTH" not in request.META
    assert "CONTENT_TYPE" not in request.META
    request.META["CONTENT_TYPE"] = "application/json"
    if content_length is not None:
        request.META["CONTENT_LENGTH"] = content_length
    return request


_UNDECLARED_LENGTHS = (
    pytest.param(None, id="no-content-length"),
    pytest.param("10", id="understated-content-length"),
)


@pytest.mark.parametrize("content_length", _UNDECLARED_LENGTHS)
@pytest.mark.parametrize(
    "max_size",
    [pytest.param(1 << 20, id="in-memory"), pytest.param(0, id="rolled-to-disk")],
)
@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_seekable_over_limit_body_is_refused_without_ever_being_read(
    view_class,
    max_size,
    content_length,
):
    """The rejecting operation itself is bounded, not just the verdict.

    The old implementation ended in ``len(request.body) > limit``, and
    ``HttpRequest.body`` performs an unbounded ``self.read()`` that copies the
    entire spooled request into one ``bytes`` value *before* the comparison can
    reject it. Django 6.0 shrinks that window with a seekable-stream size check of
    its own; the required Django 5.2.0 floor has none, so with an absent
    ``Content-Length``, an understated one, or
    ``DATA_UPLOAD_MAX_MEMORY_SIZE = None`` the package performed an
    attacker-sized allocation before enforcing its own smaller ceiling.

    The stream here is the production ``SpooledTemporaryFile`` with ``read``
    replaced by an assertion, so this row cannot pass unless the ``413`` is
    reached by size-probing alone. Both declared shapes the gate structurally
    cannot see are covered, both spool modes (in memory and rolled to disk, where
    the read would also be a disk read), and both views - the check is shared, and
    the async view is the one that would have performed that read on the event
    loop.

    The two follow-up assertions are what stop the row from degrading: ``_body``
    absent proves nothing was materialized, and a restored position proves the
    probe left the stream fit for a legitimate request to read.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    with _spooled(b"x" * (_PROBE_CAP * 16), max_size=max_size) as stream:
        request = _asgi_request(stream, content_length)

        with pytest.raises(HTTPException) as excinfo:
            view._enforce_request_body_limit(request)

        assert excinfo.value.status_code == 413
        assert excinfo.value.reason == _BODY_LIMIT_REASON
        assert hasattr(request, "_body") is False
        assert stream.tell() == 0


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_seekable_under_limit_body_reaches_strawberry_byte_for_byte(view_class):
    """The control that makes the no-read rows meaningful, and pins the success path.

    A bounded cap is worthless if it corrupts or truncates the bodies it allows,
    and the seekable branch's whole risk is the position it moves: a probe that
    forgot to rewind would leave ``request.body`` empty and every legitimate
    request would 400 as malformed JSON. Reading the body back byte-for-byte -
    from a payload carrying every byte value, which a stray decode or text-mode
    round trip would mangle - is the strongest available statement that Strawberry
    receives exactly what the client sent. The payload is also exactly at the
    limit, so the row doubles as this branch's ``>``-not-``>=`` boundary proof.

    ``_body`` absent *before* the read is the second half: the cap sized the
    stream without materializing anything, so the allocation that follows is
    Django's own, performed against a body already proven to be within the limit.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    with _spooled(_UNDER_LIMIT_BODY, spool_class=tempfile.SpooledTemporaryFile) as stream:
        request = _asgi_request(stream, None)

        view._enforce_request_body_limit(request)

        assert hasattr(request, "_body") is False
        assert request.body == _UNDER_LIMIT_BODY


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_an_undeclared_seekable_stream_is_still_size_probed_rather_than_read(view_class):
    """The Python 3.10 floor's ASGI body file is size-probed, not read.

    ``SpooledTemporaryFile`` gained ``seekable()`` only in 3.11, so a probe that
    required the method would quietly drop the ASGI spool onto the read branch at
    the exact interpreter floor this card supports - passing on the development
    stack and losing the guarantee where it matters most. The stand-in reproduces
    that shape (no ``seekable``, working ``seek`` / ``tell``) and records reads, so
    an empty ``requested`` list is direct evidence the fallback probe ran.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = _UndeclaredSeekableStream(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    with pytest.raises(HTTPException, match="request-body limit"):
        view._enforce_request_body_limit(request)

    assert stream.requested == []
    assert stream.delivered == 0
    assert hasattr(request, "_body") is False


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_non_seekable_over_limit_body_reads_at_most_one_byte_past_the_limit(view_class):
    """A stream that can only be measured by reading is read to ``limit + 1`` and no further.

    One byte past the limit is the least information that distinguishes "exactly
    at the limit" (legal) from "over it", so it is the correct bound rather than a
    convenient one. The three assertions are the whole security property: no more
    than ``limit + 1`` bytes were ever handed over, bytes are demonstrably still
    unread in the stream, and no ``_body`` exists - the collected chunks are never
    joined, so no over-limit ``bytes`` value is allocated even transiently.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = _RecordingNonSeekableStream(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    with pytest.raises(HTTPException, match="request-body limit"):
        view._enforce_request_body_limit(request)

    assert stream.delivered == _PROBE_CAP + 1
    assert max(stream.requested) <= _PROBE_CAP + 1
    assert stream.unread > 0
    assert hasattr(request, "_body") is False


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_non_seekable_under_limit_body_is_handed_back_as_a_rewound_stream(view_class):
    """An allowed bounded read gives the bytes back as a stream, not as Django's cache.

    The bounded branch is the one that has to hand its bytes back, and *how* is a
    correctness decision rather than a detail. Pre-filling ``request._body`` - the
    obvious shape, and what ``HttpRequest.body`` itself leaves behind - makes that
    property short-circuit on its cache, which silently disables Django's own
    ``DATA_UPLOAD_MAX_MEMORY_SIZE`` ceiling for every request that took this
    branch. A package cap must add a ceiling, never remove one, so the consumed
    stream is replaced with a rewound ``BytesIO`` and ``_read_started`` is reset to
    the value the request was built with - a state that is true again, because the
    installed stream is complete and unread.

    ``_body`` absent afterwards is therefore the assertion that matters: Django's
    property has not run yet and will run in full. The live proof that its ceiling
    still fires is
    ``test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce``,
    which caught exactly this when the cache was pre-filled.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = _RecordingNonSeekableStream(_UNDER_LIMIT_BODY)
    request = _asgi_request(stream, None)

    view._enforce_request_body_limit(request)

    assert hasattr(request, "_body") is False
    assert request._read_started is False
    assert isinstance(request._stream, BytesIO)
    assert stream.closed is True
    assert stream.delivered == len(_UNDER_LIMIT_BODY)

    assert request.body == _UNDER_LIMIT_BODY
    assert request._body == _UNDER_LIMIT_BODY
    assert request.read() == _UNDER_LIMIT_BODY


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_an_unmeasurable_stream_falls_back_to_the_bounded_read(view_class):
    """A stream that cannot report its position is read, not waved through.

    "Unmeasurable" must never resolve to "assume it fits". The stand-in has no
    ``seekable`` and a ``tell()`` that raises, which is what a raw WSGI pipe
    presents; the cap has to reach the bounded read and reject from there.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = _UnmeasurableStream(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    with pytest.raises(HTTPException, match="request-body limit"):
        view._enforce_request_body_limit(request)

    assert stream.delivered == _PROBE_CAP + 1


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_stream_that_probes_as_empty_is_read_rather_than_believed(view_class):
    """A size probe may never answer "the body is empty" on its own.

    ``_measured_remaining``'s contract is that ``None`` means "ask the bounded
    read instead", never "the body is empty" - and a probed count of ``0`` is the
    one answer that breaks it, because ``body_exceeds_limit`` reads it as "within
    the limit" while nothing has been read. The refused stream then goes to
    ``HttpRequest.body`` with **no package bound at all**, whose only ceiling at
    the Django 5.2.0 floor is the ``CONTENT_LENGTH`` the cap exists precisely not
    to trust. The old ``max(end - position, 0)`` produced exactly that answer for
    a stream that reports a position but cannot take one.

    Verifying a zero costs one ``read`` call, so the fix verifies it, and this row
    asserts the verification is itself bounded rather than merely non-empty: the
    4096-byte body is refused after ``limit + 1`` bytes, with bytes demonstrably
    still unread and nothing materialized. A status-only assertion would pass
    against a version that read the whole payload to reach the same ``413``.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = _MisreportingSizeStream(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    with pytest.raises(HTTPException, match="request-body limit"):
        view._enforce_request_body_limit(request)

    assert stream.delivered == _PROBE_CAP + 1
    assert max(stream.requested) <= _PROBE_CAP + 1
    assert stream.unread > 0
    assert hasattr(request, "_body") is False


def _assert_one_unmeasurable_body_was_recorded(
    caplog,
    stream,
    message,
    *,
    exc_type,
):
    """The shape BOTH of the body gate's operator signals share, asserted once.

    ``_request_body.py`` refuses two ways it cannot describe on the wire - an
    incoherent size probe and a bounded read that could not complete - and each is
    by design indistinguishable from an ordinary over-limit rejection to the client
    (Decision 9's non-attributability). So an operator debugging a ``413`` for a
    request that is not oversized has nothing to go on unless the server records
    the distinction, and the two records are therefore held to one contract: one
    record, at ``WARNING``, carrying the specific message object and the stream's
    own class name.

    The message is asserted by IDENTITY rather than by a re-typed string, so a
    reworded record still pins the contract; ``args`` is what keeps the class name
    - the only actionable detail, since the culprit is whatever the ASGI server or
    a middleware installed - from being dropped in a later edit; and the level
    keeps either signal from drifting to ``logger.exception``'s ``ERROR``, which
    would file a broken client as a package failure.

    ``exc_type`` is the ONE axis the two differ on, so it is a parameter rather
    than a second copy of the function: ``None`` asserts no traceback was attached,
    an exception class asserts the attached one is it.
    """
    records = [record for record in caplog.records if record.name == "django_strawberry_framework"]

    assert len(records) == 1, caplog.records
    assert records[0].levelno == logging.WARNING
    assert records[0].msg is message
    assert records[0].args == (type(stream).__name__,)
    if exc_type is None:
        assert records[0].exc_info is None
    else:
        assert isinstance(records[0].exc_info[1], exc_type)


def _assert_the_corrupted_probe_was_recorded(caplog, stream):
    """Exactly one ``WARNING`` naming the probe outcome and the stream that caused it.

    No traceback, and that is the difference from the bounded read's twin rather
    than an omission: a restore that returned the wrong position never raised, so
    there is no exception to attach and ``exc_info is None`` is the assertion that
    keeps this from being "fixed" into one that carries a stale traceback.
    """
    _assert_one_unmeasurable_body_was_recorded(
        caplog,
        stream,
        _CORRUPTED_PROBE_LOG_MESSAGE,
        exc_type=None,
    )


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_stream_reporting_a_position_past_its_end_is_refused_rather_than_read(
    view_class,
    caplog,
):
    """The other incoherent direction: an unverifiable restore fails CLOSED.

    ``max(end - position, 0)`` clamped a negative measurement - a ``tell()`` that
    over-reports - to "no bytes remaining, allowed", so a full body reached
    ``HttpRequest.body`` unbounded. The pair is judged rather than clamped now, and
    the verdict is the third probe outcome rather than the second:
    the position this stream reports is a lie, so the restore lands somewhere the
    stream did not start, the verifying ``tell()`` says so, and the request is
    refused with the package's own ``413``.

    Falling through to a bounded read instead - which is what the two-state version
    did - meant reading from an offset past the body's end and handing Strawberry
    an **empty** body the client never sent, then answering ``400`` at the parse.
    Both outcomes are safe, but only one of them is honest about what happened, and
    "the package could not measure this body" is a body-limit rejection rather than
    a malformed-document one. The witnesses are that NOTHING was read and nothing
    was materialized: a stream whose coordinates are incoherent is not a stream the
    package will read bytes out of.

    The server-side record is asserted too: the wire cannot
    carry the distinction, so the log is the only place it exists.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = _OverReportingPositionStream(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    with caplog.at_level(logging.WARNING, logger="django_strawberry_framework"):
        with pytest.raises(HTTPException) as excinfo:
            view._enforce_request_body_limit(request)

    assert excinfo.value.status_code == 413
    assert excinfo.value.reason == _BODY_LIMIT_REASON
    assert stream.requested == []
    assert stream.delivered == 0
    assert hasattr(request, "_body") is False
    _assert_the_corrupted_probe_was_recorded(caplog, stream)


@pytest.mark.parametrize(
    "stream_class",
    [
        pytest.param(_CapabilityQueryRaisingStream, id="seekable-raises"),
        pytest.param(_UnseekableToEndStream, id="seek-to-end-raises"),
        pytest.param(_UnnumberedSeekStream, id="unnumbered-end-position"),
    ],
)
@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read(
    view_class,
    stream_class,
):
    """A failed probe is a ``413`` from a bounded read, never a ``500``.

    Three failure sites, one classification. ``seekable()`` raising and an
    unnumbered end position both leave the stream untouched; the seek to the end
    raising leaves it unknown until the restore proves otherwise - and here the
    restore does. In all three the position is provably where the request started,
    so the bounded read is licensed and supplies the bound.

    The old implementation called ``seekable()`` and both ``seek``s unguarded, so
    each of these streams turned a request into an unhandled ``500``. The bound is
    asserted rather than just the status: exactly
    ``limit + 1`` bytes are read, bytes are demonstrably left unread, and nothing
    is materialized.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = stream_class(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    with pytest.raises(HTTPException) as excinfo:
        view._enforce_request_body_limit(request)

    assert excinfo.value.status_code == 413
    assert excinfo.value.reason == _BODY_LIMIT_REASON
    assert stream.delivered == _PROBE_CAP + 1
    assert max(stream.requested) <= _PROBE_CAP + 1
    assert stream.unread > 0
    assert hasattr(request, "_body") is False


@pytest.mark.parametrize(
    "stream_class",
    [
        pytest.param(_ArithmeticRaisingPositionStream, id="subtraction-raises"),
        pytest.param(_ComparisonRaisingPositionStream, id="comparison-raises"),
    ],
)
@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate(
    view_class,
    stream_class,
):
    """No foreign numeric protocol is executed on a probed position, at all.

    The probe used to guard the subtraction alone, and only against ``TypeError``,
    while the ``remaining <= 0`` comparison ran outside every guard. Both
    expressions execute code belonging to whatever object the stream handed back,
    so a position whose ``__sub__`` or ``__le__`` raises anything else turned the
    body boundary into an unrelated ``500`` - the exact failure mode the rest of
    this module's totality exists to prevent, reached through arithmetic instead of
    through a method call.

    Guarding the expressions is not the fix, because a guard still runs the foreign
    code and a plausible-but-wrong answer from it would be believed. Only the exact
    built-in ``int`` both production streams report is accepted, so these two
    positions - ``int`` subclasses, which is what gets past an ``isinstance``
    check - are never operated on: the verdict is "unmeasurable", and the bounded
    read supplies the bound, with its own ``limit + 1`` ceiling asserted rather
    than just the status.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = stream_class(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    with pytest.raises(HTTPException) as excinfo:
        view._enforce_request_body_limit(request)

    assert excinfo.value.status_code == 413
    assert excinfo.value.reason == _BODY_LIMIT_REASON
    assert stream.delivered == _PROBE_CAP + 1
    assert max(stream.requested) <= _PROBE_CAP + 1
    assert stream.unread > 0
    assert hasattr(request, "_body") is False


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_probe_that_cannot_restore_the_position_refuses_instead_of_reading(view_class, caplog):
    """The fail-closed state: a failed restore ends the request.

    The one outcome that must never become a bounded read. The probe has already
    moved this stream to its end and the restore raises, so every byte a read
    could still return is the wrong byte - reading anyway would have handed
    Strawberry an empty body in place of the client's, which is a silent
    substitution rather than a rejection.

    "Not measurable" and "not readable" therefore have to be different answers,
    which is why the probe reports three outcomes and not two. The witness is that
    no read was even attempted: the refusal comes from the probe's verdict, not
    from a read that happened to come back empty.

    The second stand-in for the same server-side record, so the
    log is pinned by both ``CORRUPTED`` shapes rather than by whichever one a later
    refactor happens to keep - and the stream class in ``args`` differs between
    them, which is the detail an operator needs.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = _UnrestorableStream(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    with caplog.at_level(logging.WARNING, logger="django_strawberry_framework"):
        with pytest.raises(HTTPException) as excinfo:
            view._enforce_request_body_limit(request)

    assert excinfo.value.status_code == 413
    assert excinfo.value.reason == _BODY_LIMIT_REASON
    assert stream.requested == []
    assert stream.delivered == 0
    assert hasattr(request, "_body") is False
    assert request._stream is stream
    _assert_the_corrupted_probe_was_recorded(caplog, stream)


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_genuinely_empty_body_is_allowed_by_one_bounded_read(view_class):
    """The control that keeps "never believe a zero" from becoming "always read".

    An empty POST body is legal - it is refused later, by the JSON parse, not by
    the cap - so the zero-verification has to end in "allowed" for an honest
    stream and it has to cost almost nothing. Both are asserted here: exactly one
    ``read``, sized at the ``limit + 1`` ceiling every bounded read uses, and a
    body Django still serves as ``b""``.

    The ``requested`` list is also what makes this row fail against the clamping
    version, where the probe's zero was believed and no read happened at all - so
    the control is a statement about the new code path rather than a restatement
    of the old behavior.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = _UndeclaredSeekableStream(b"")
    request = _asgi_request(stream, None)

    view._enforce_request_body_limit(request)

    assert stream.requested == [_PROBE_CAP + 1]
    assert stream.delivered == 0
    assert stream.closed is True
    assert request.body == b""


def _assert_the_unreadable_stream_was_recorded(caplog, stream):
    """Exactly one ``WARNING`` naming the unreadable stream, with its traceback attached.

    The bounded read's twin of :func:`_assert_the_corrupted_probe_was_recorded`,
    and the attached traceback is the difference between them: a failed read always
    has a live exception, and WHICH exception it is - Django's own
    ``UnreadablePostError``, wrapping the stream's ``OSError`` - is the only thing
    that tells an operator the client's stream died rather than the package's limit
    being wrong.
    """
    _assert_one_unmeasurable_body_was_recorded(
        caplog,
        stream,
        _UNREADABLE_STREAM_LOG_MESSAGE,
        exc_type=UnreadablePostError,
    )


@pytest.mark.parametrize(
    "stream_class",
    [
        pytest.param(_ReadRaisingStream, id="raises-at-zero-bytes"),
        pytest.param(_ReadRaisingAfterPrefixStream, id="raises-after-a-partial-prefix"),
    ],
)
@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_request_stream_that_cannot_be_read_is_refused_rather_than_escaping(
    view_class,
    stream_class,
    caplog,
):
    """A broken client stream is the controlled ``413``, never an unhandled ``500``.

    The bounded read is the fallback the capability probe *selects*, so it has to
    be as total as the probe is. It was not: ``request.read`` was called unguarded,
    and Django turns a stream ``OSError`` into ``UnreadablePostError``, which is
    not an ``HTTPException`` - so it propagated through the boundary, past
    upstream's ``except HTTPException``, and out of the view. Under Django's
    handler an ordinary client that hung up mid-POST therefore produced a ``500``
    and an error log from the one code path whose entire job is to refuse
    politely. Nothing was executed and no cap was bypassed, which is why this is
    the response and the attribution being wrong rather than a hole - and why the
    fix is the module's documented fail-closed ``bool``, not a new exception type.

    Both failure moments are covered because they leave different residue: raising
    at zero bytes leaves nothing collected, while raising after a partial prefix
    leaves the loop holding a fragment of a body it must not pass on. The
    assertions are the whole contract - the selected status and reason, a read
    count that shows the loop stopped at the failure instead of retrying, and a
    request from which NO body can be obtained at all: ``_body`` was never filled,
    the consumed stream was not swapped for the collected prefix, and
    ``request.body`` therefore raises Django's own ``RawPostDataException``. That
    last one is what makes "no partial body reached Strawberry" a proof rather than
    an inference about ordering.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = stream_class(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    with caplog.at_level(logging.WARNING, logger="django_strawberry_framework"):
        with pytest.raises(HTTPException) as excinfo:
            view._enforce_request_body_limit(request)

    assert excinfo.value.status_code == 413
    assert excinfo.value.reason == _BODY_LIMIT_REASON
    # No unbounded retry: the loop asked once more than it had already succeeded
    # at, and stopped on the failure.
    assert len(stream.requested) <= 2
    assert max(stream.requested) <= _PROBE_CAP + 1
    # No partial body is handed on, in either of the two ways it could have been.
    assert hasattr(request, "_body") is False
    assert request._stream is stream
    assert stream.closed is False
    with pytest.raises(RawPostDataException):
        request.body  # the raise IS the assertion
    _assert_the_unreadable_stream_was_recorded(caplog, stream)


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_body_already_cached_by_middleware_is_measured_from_the_cache_and_refused(view_class):
    """The one shape the cap cannot bound, and the only thing left to do about it.

    A consumer middleware that reads ``request.POST`` (or ``request.body``) on the
    way in materializes ``_body`` through ``HttpRequest.body`` - an allocation that
    has already happened by the time ``run`` is entered and cannot be undone. It
    used to be Django's own ``CsrfViewMiddleware`` that did this, for every
    cookie-bearing ``application/x-www-form-urlencoded`` POST; the ``csrf_exempt``
    / ``csrf_protect`` re-entry moved that read behind the boundary, so what is
    left on this rung is a read no application-level ordering can precede. The package must still refuse to
    *process* it, measured off the cache rather than by re-reading, which the
    unreadable stream proves: the cache is consulted and the stream is not
    touched. The under-limit direction in the same row is what shows the cached
    branch is a measurement rather than a blanket rejection.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    with _spooled(b"unused") as stream:
        over = _asgi_request(stream, None)
        over._body = b"x" * (_PROBE_CAP + 1)

        with pytest.raises(HTTPException, match="request-body limit"):
            view._enforce_request_body_limit(over)

        under = _asgi_request(stream, None)
        under._body = b"x" * _PROBE_CAP
        view._enforce_request_body_limit(under)

        assert under.body == b"x" * _PROBE_CAP
        assert stream.tell() == 0


def test_the_cap_defers_on_a_stream_some_other_component_already_consumed():
    """A half-consumed stream is deferred, not translated into a misleading ``413``.

    Once something has read from the stream without caching ``_body``,
    ``HttpRequest.body`` itself raises ``RawPostDataException``, so nothing
    downstream can process the request either - there is no bypass to close here.
    What the cap must not do is measure by calling ``request.body`` and surface
    another component's error as a body-limit rejection, which is precisely what
    the previous ``len(request.body)`` implementation did. The second half asserts
    the honest outcome is still reached by whoever asks for the body.
    """
    view = _capped_view(_PROBE_CAP)
    with _spooled(b"x" * (_PROBE_CAP * 16), spool_class=tempfile.SpooledTemporaryFile) as stream:
        request = _asgi_request(stream, None)
        request.read(4)

        view._enforce_request_body_limit(request)

        with pytest.raises(RawPostDataException):
            request.body  # the raise IS the assertion


def test_the_cap_defers_on_a_request_that_carries_no_stream_at_all():
    """A synthetic ``HttpRequest`` has no ``_stream``, and that is not an error.

    ``HttpRequest.__init__`` sets neither ``_stream`` nor ``_read_started`` - only
    ``WSGIRequest`` / ``ASGIRequest`` do - so a request built by hand (a consumer
    helper, a management command, a test harness) reaches the cap with no byte
    source to measure. Deferring keeps the cap from inventing an
    ``AttributeError`` on a shape Django itself tolerates.
    """
    view = _capped_view(_PROBE_CAP)
    request = HttpRequest()
    request.method = "POST"

    view._enforce_request_body_limit(request)

    assert hasattr(request, "_body") is False


# ---------------------------------------------------------------------------
# The strict UTF-8 wire contract is the package VIEW's, so it
# does not share the ``APPLY_UPSTREAM_PATCHES`` lifecycle of the upstream-bug
# workarounds. The wire outcomes are live in fakeshop; what only this tier can
# state is WHICH mechanism refused which byte shape, because all nine rejected
# shapes carry the identical status and message by design.
# ---------------------------------------------------------------------------

_WIRE_SHAPES = (
    pytest.param('{"a": 1}'.encode("utf-16"), UnicodeDecodeError, id="utf-16-with-bom"),
    pytest.param('{"a": 1}'.encode("utf-32"), UnicodeDecodeError, id="utf-32-with-bom"),
    pytest.param(b'{"a": "\x80"}', UnicodeDecodeError, id="invalid-utf8-byte"),
    pytest.param(bytes(range(256)) * 4, UnicodeDecodeError, id="raw-binary"),
    pytest.param('{"a": 1}'.encode("utf-16-le"), json.JSONDecodeError, id="utf-16-le-no-bom"),
    pytest.param('{"a": 1}'.encode("utf-16-be"), json.JSONDecodeError, id="utf-16-be-no-bom"),
    pytest.param('{"a": 1}'.encode("utf-32-le"), json.JSONDecodeError, id="utf-32-le-no-bom"),
    pytest.param('{"a": 1}'.encode("utf-32-be"), json.JSONDecodeError, id="utf-32-be-no-bom"),
    pytest.param(b"\xef\xbb\xbf" + b'{"a": 1}', json.JSONDecodeError, id="utf-8-bom"),
)


@contextlib.contextmanager
def _strawberry_patch_opted_out():
    """The runtime state ``APPLY_UPSTREAM_PATCHES = {"strawberry": False}`` produces.

    The patch installs from ``AppConfig.ready()``, so flipping the setting inside
    a test cannot un-install it; the honest simulation restores upstream's own two
    methods *and* sets the setting, so a stray ``apply()`` stays a no-op for the
    duration. What is left running is exactly what a consumer who opted out would
    be running.
    """
    saved_parse_json = BaseView.__dict__["parse_json"]
    saved_parse_query_params = BaseView.__dict__["parse_query_params"]
    override = override_settings(
        DJANGO_STRAWBERRY_FRAMEWORK={"APPLY_UPSTREAM_PATCHES": {"strawberry": False}},
    )
    try:
        BaseView.parse_json = patches._original_parse_json
        BaseView.parse_query_params = patches._original_parse_query_params
        with override:
            yield
    finally:
        BaseView.parse_json = saved_parse_json
        BaseView.parse_query_params = saved_parse_query_params


@pytest.mark.parametrize(("body", "cause"), _WIRE_SHAPES)
@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_the_package_view_rejects_every_non_utf8_wire_shape(view_class, body, cause):
    """The wire matrix, now owned by the view: every non-UTF-8 shape 400s, and why.

    The executable form of spec-046 Decision 9's measured-behavior table and of
    Decision 10 reason (a). Status and message are identical across all nine rows
    - deliberately, so one byte sequence has one interpretation at every hop - so
    ``__cause__`` is the only thing that records the split:

    * ``UnicodeDecodeError`` - the view's own strict decode refused the bytes (a
      BOM'd multi-byte form, an invalid byte, raw binary);
    * ``json.JSONDecodeError`` - the bytes decoded cleanly and upstream's own
      ``json.loads`` refused the resulting text (BOM-less multi-byte forms, and
      the UTF-8 BOM that Decision 10 declines to strip).

    Pinning the second group matters because that rejection is *inherited*: a
    future stdlib that tolerated a leading U+FEFF, or NUL-studded text, would
    silently turn these 400s into 200s with no package change at all. Both
    views run every row because the two transports share the one mixin method and
    must not be able to drift.
    """
    view = view_class(schema=SCHEMA)

    with pytest.raises(HTTPException) as excinfo:
        view.parse_json(body)

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == _JSON_PARSE_REASON
    assert type(excinfo.value.__cause__) is cause


@pytest.mark.parametrize(("body", "cause"), _WIRE_SHAPES)
@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_the_wire_contract_holds_with_the_upstream_patches_opted_out(view_class, body, cause):
    """The identical nine rows with ``{"strawberry": False}`` in effect.

    The strict decode used to live inside
    ``_patched_parse_json``, so a consumer who disabled the package's *upstream
    bug workarounds* also disabled a permanent security policy and silently got
    UTF-16 / UTF-32 acceptance back. With the policy on the view, the whole matrix
    - including ``__cause__``, i.e. by which mechanism - is unchanged with the
    patch pair un-installed: the ``UnicodeDecodeError`` rows are the view's own
    decode, and the ``json.JSONDecodeError`` rows are upstream's own ``except``,
    which needs no patch to raise the same ``400``.

    The mounted, over-the-wire version of this row is live in
    ``examples/fakeshop/test_query/test_transport_api.py``.
    """
    view = view_class(schema=SCHEMA)

    with _strawberry_patch_opted_out():
        with pytest.raises(HTTPException) as excinfo:
            view.parse_json(body)

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == _JSON_PARSE_REASON
    assert type(excinfo.value.__cause__) is cause


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_the_package_view_parses_valid_utf8_including_multibyte_unchanged(view_class):
    """The success path is untouched, and the contract is UTF-8 rather than ASCII.

    A control built the usual way would be vacuous: ``json.dumps``'s default
    ``ensure_ascii=True`` emits ``\\u00e9`` escapes, so it would pass even under an
    ``"ascii"`` codec. This body carries a genuine ``C3 A9`` on the wire, asserted
    before the parse.
    """
    view = view_class(schema=SCHEMA)
    multibyte = json.dumps({"a": "caf\u00e9"}, ensure_ascii=False).encode("utf-8")
    assert max(multibyte) > 0x7F

    assert view.parse_json(b'{"a": 1}') == {"a": 1}
    assert view.parse_json(multibyte) == {"a": "caf\u00e9"}


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_the_package_view_hands_upstream_a_str_for_a_bytes_body(view_class):
    """Attribution: the decode happens at the view, so upstream never sees ``bytes``.

    Recording what upstream's ``parse_json`` actually receives is the crispest
    available proof, because a status-code or message assertion cannot distinguish
    the two mechanisms. Once the delegate only ever sees ``str``,
    ``json.loads``'s RFC 8259 encoding auto-detection is unreachable by
    construction rather than by a rejection branch - which is why the whole
    contract adds no encoding sniffer.
    """
    view = view_class(schema=SCHEMA)
    seen = []

    def _recorder(self, data):
        seen.append(data)
        return {"recorded": True}

    with mock.patch.object(BaseView, "parse_json", _recorder):
        assert view.parse_json(b'{"a": 1}') == {"recorded": True}

    assert seen == ['{"a": 1}']
    assert isinstance(seen[0], str)


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_the_package_view_passes_a_str_body_through_by_identity(view_class):
    """A ``str`` input reaches upstream as the **same object**, never a round trip.

    Upstream's GET ``variables`` / ``extensions`` parses and the multipart
    ``operations`` / ``map`` form fields arrive already decoded by Django, and
    spec-046 Decision 9 passes them through untouched. Asserting object identity
    rather than equality is what rules out an incidental encode-then-decode cycle
    on those paths.
    """
    view = view_class(schema=SCHEMA)
    body = '{"a": 1}'
    seen = []

    def _recorder(self, data):
        seen.append(data)
        return {"recorded": True}

    with mock.patch.object(BaseView, "parse_json", _recorder):
        view.parse_json(body)

    assert seen[0] is body


def test_the_wire_reason_is_upstreams_own_parse_json_literal():
    """The 400's reason is pinned against what upstream actually raises, not a copy.

    Identity with upstream's message is the contract (spec-046 Decision 9): a body
    the package's strict decode refused and a body upstream's ``json.loads``
    refused must be indistinguishable on the wire, so ``__cause__`` stays the only
    discriminator. Two named constants reproduce that literal - the view's and the
    patch module's, which stay separate so neither module has to import the other
    - and both are checked here against upstream's live raise, so an upstream
    message change fails loudly instead of quietly splitting one contract into
    two.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._original_parse_json(BaseView(), "{not valid json")

    assert excinfo.value.reason == _JSON_PARSE_REASON
    assert patches._UPSTREAM_JSON_PARSE_REASON == _JSON_PARSE_REASON


def _json_request(raw):
    """A real request carrying ``raw`` as its body, for the adapter rows below."""
    return RequestFactory().post("/graphql/", data=raw, content_type="application/json")


def test_the_sync_view_hands_parse_json_raw_bytes_in_every_patch_state():
    """The sync transport's body source is the package view's own.

    ``parse_json`` can only enforce the strict decode over bytes it is given, and
    on the sync transport upstream's request adapter decides that: its ``body``
    property returns ``self.request.body.decode()``, so an undecodable body raises
    ``UnicodeDecodeError`` inside a *property* - unreachable by ``dispatch``'s
    ``except HTTPException`` - and ``parse_json`` never sees bytes at all. With
    ``APPLY_UPSTREAM_PATCHES = False`` that made the mounted sync view answer
    ``500`` rather than the contract's ``400``, measured, while async answered
    ``400``.

    The package view therefore sets upstream's own ``request_adapter_class`` seam
    to a one-property subclass. This row is the attribution the live rows cannot
    make: with upstream's eagerly-decoding getter reinstalled - exactly the
    patches-off state - the package adapter still yields the untouched bytes while
    upstream's own adapter raises on the identical request. The subclass check is
    what keeps it a one-property override rather than a fork of the other ten
    adapter members.
    """
    raw = '{"a": 1}'.encode("utf-16")
    saved = DjangoHTTPRequestAdapter.__dict__["body"]

    assert DjangoGraphQLView.request_adapter_class is _RawBodyRequestAdapter
    assert issubclass(_RawBodyRequestAdapter, DjangoHTTPRequestAdapter)

    try:
        DjangoHTTPRequestAdapter.body = property(cross_web_patches._original_body_fget)
        assert cross_web_patches._patch_is_installed() is False

        body = _RawBodyRequestAdapter(_json_request(raw)).body
        with pytest.raises(UnicodeDecodeError):
            DjangoHTTPRequestAdapter(_json_request(raw)).body
    finally:
        DjangoHTTPRequestAdapter.body = saved

    assert body == raw
    assert isinstance(body, bytes)


async def test_the_async_view_needs_no_adapter_override_because_upstream_hands_bytes():
    """The asymmetry is upstream's, and pinned rather than assumed.

    Only the sync view overrides ``request_adapter_class``, which reads like an
    oversight unless the reason is asserted: upstream's
    ``AsyncDjangoHTTPRequestAdapter.get_body`` already returns
    ``self.request.body`` untouched, so the async transport reaches ``parse_json``
    with raw bytes with or without any patch - which is why the wire contract never
    degraded there. If a future upstream release decoded in ``get_body`` too, or if
    someone "symmetrized" the views by pointing the async one at the sync adapter,
    this row fails instead of the async transport silently losing the 400.
    """
    raw = '{"a": 1}'.encode("utf-16")

    assert AsyncDjangoGraphQLView.request_adapter_class is AsyncDjangoHTTPRequestAdapter

    adapter = AsyncDjangoHTTPRequestAdapter(_json_request(raw))
    assert await adapter.get_body() == raw


def test_both_package_views_resolve_parse_json_to_the_one_shared_mixin_method():
    """Sync/async parity is structural: one owner above upstream, on both views.

    The behavioral colours live over real requests (sync in
    ``examples/fakeshop/test_query/test_products_api.py``, async in
    ``test_transport_api.py``). This row closes the regression channel those
    cannot see: an intermediate class - a future upstream ``GraphQLView`` method,
    or a second package override - defining ``parse_json`` on one transport only
    would silently strip the wire contract from that transport while every live row
    on the other stayed green. Asserting the exact two-owner MRO chain, in order,
    fails the moment such a class appears, and also pins that the mixin *delegates*
    to upstream rather than replacing it.
    """
    from django_strawberry_framework import views as views_module

    mixin = views_module._RequestBodyBoundaryMixin

    for view_class in (DjangoGraphQLView, AsyncDjangoGraphQLView):
        assert view_class.parse_json is mixin.parse_json
        owners = [klass for klass in view_class.__mro__ if "parse_json" in vars(klass)]
        assert owners == [mixin, BaseView]


# ---------------------------------------------------------------------------
# Multipart: the effective form encoding is a codec question,
# not a string-matching one, so the alias matrix is a pure-function contract
# that belongs here. The wire outcomes - real multipart requests carrying a
# malformed byte, an explicit Latin-1 declaration, genuine multibyte UTF-8, and
# an escaped replacement character - are live in
# ``examples/fakeshop/test_query/test_transport_api.py``.
#
# The gate is TWO independent conditions, so each one and
# each sub-rung of the effective encoding gets its own row that fails on its own.
# One row used to pin two rungs at once, which means removing either of them cost
# the suite the same single failure and neither was really pinned:
#
#   * the declared charset            -> ``..._is_refused_even_when_django_would_decode_utf8``
#     (plus the alias matrix below, and the M1 row for the masking direction)
#   * ``request.encoding``            -> ``..._non_utf8_request_encoding_is_refused_on_its_own``
#     and ``..._does_not_mask_a_middleware_set_request_encoding``
#   * ``settings.DEFAULT_CHARSET``    -> ``..._reconfigured_default_charset_is_refused_...``
# ---------------------------------------------------------------------------

_DECLARED_CHARSETS = (
    pytest.param("utf-8", True, id="utf-8"),
    pytest.param("UTF-8", True, id="uppercase"),
    pytest.param("utf8", True, id="unhyphenated"),
    pytest.param("u8", True, id="obscure-alias"),
    pytest.param("iso-8859-1", False, id="latin-1"),
    pytest.param("utf-16", False, id="utf-16"),
    pytest.param("utf-8-sig", False, id="utf-8-sig"),
    pytest.param("no-such-codec", False, id="unknown-name"),
)


_MULTIPART_BOUNDARY = "BoUnDaRy"


def _multipart_body(raw):
    """A real single-field multipart body carrying ``raw`` as ``operations``.

    Hand-built rather than produced by ``RequestFactory.post`` because the whole
    subject of the rows that use it is a byte sequence a client sent and a codec
    name the client declared, and ``post`` re-encodes the payload with that
    declared charset instead of putting it on the wire. Only the rows that need
    Django to *actually decode* the form use this; the header-only rows stop at
    the gate and use a one-byte payload.
    """
    disposition = 'Content-Disposition: form-data; name="operations"'
    return (
        f"--{_MULTIPART_BOUNDARY}\r\n{disposition}\r\n\r\n".encode()
        + raw
        + f"\r\n--{_MULTIPART_BOUNDARY}--\r\n".encode()
    )


def _multipart_request(
    charset=None,
    *,
    encoding=None,
    method="POST",
    data=b"x",
):
    """A multipart request whose declared ``Content-Type`` carries ``charset``.

    Built through ``generic`` rather than ``post`` for one reason that is itself
    part of the contract: ``RequestFactory.post`` encodes the payload *with* the
    declared charset, so it cannot express an unusable codec name - the very
    declaration a real client is free to send and that Django itself silently
    drops. ``generic`` puts the header on the request untouched, which is what
    the endpoint has to cope with.

    The payload defaults to a single byte rather than empty because ``generic``
    only populates ``CONTENT_TYPE`` ``if data`` - and the content type is the
    entire subject of most rows below, which stop at the header check.

    ``encoding=`` stands in for a consumer middleware assigning
    ``request.encoding``, Django's documented per-request override. It is applied
    AFTER construction on purpose: that is the only order a middleware can act
    in, and it is what overwrites the promotion
    ``HttpRequest._set_content_type_params`` performed from the declaration.
    ``method=`` exists for the GET carve-out row.
    """
    content_type = f"multipart/form-data; boundary={_MULTIPART_BOUNDARY}"
    if charset is not None:
        content_type = f"{content_type}; charset={charset}"
    request = RequestFactory().generic(method, "/graphql/", data=data, content_type=content_type)
    if encoding is not None:
        request.encoding = encoding
    return request


@pytest.mark.parametrize(("charset", "accepted"), _DECLARED_CHARSETS)
def test_only_codecs_that_canonicalize_to_utf8_are_accepted_as_a_form_encoding(charset, accepted):
    """The declared charset is resolved through ``codecs``, not compared as a string.

    Every alias Python calls UTF-8 is accepted, including ones the package has
    never heard of, and everything else is refused - ``utf-8-sig`` included,
    because it is a *different* codec that would silently eat the BOM Decision 10
    deliberately refuses. An unknown codec name is refused rather than ignored:
    Django's own ``_set_content_type_params`` drops an unusable charset and decodes
    with ``DEFAULT_CHARSET`` instead, so accepting the request would mean honouring
    a declaration nobody honoured.

    The reason is the shared one on purpose (Decision 9): a caller must not be able
    to tell which of the endpoint's refusals it hit by reading the message.
    """
    view = DjangoGraphQLView(schema=SCHEMA)
    request = _multipart_request(charset)

    if accepted:
        view._enforce_multipart_form_encoding(request)
        return

    with pytest.raises(HTTPException) as excinfo:
        view._enforce_multipart_form_encoding(request)

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == _JSON_PARSE_REASON


_NON_STRING_ENCODINGS = (
    pytest.param(b"utf-8", id="bytes-lifted-off-a-header"),
    pytest.param(42, id="int"),
    pytest.param(object(), id="arbitrary-object"),
)


@pytest.mark.parametrize("encoding", _NON_STRING_ENCODINGS)
def test_a_non_string_effective_encoding_is_refused_rather_than_escaping_as_a_typeerror(encoding):
    """``codecs.lookup`` raises ``TypeError``, not ``LookupError``, on a non-string.

    ``request.encoding`` is a public settable attribute with no type coercion, so
    the value ``_form_encoding_is_utf8`` resolves is whatever consumer middleware
    assigned - and ``b"utf-8"`` lifted straight off a header is the plausible slip
    rather than a synthetic one. ``codecs.lookup`` refuses every non-``str``
    argument with ``TypeError``, which no ``LookupError`` handler catches.

    The refusal is asserted at the boundary rather than on
    ``_canonicalizes_to_utf8``'s return value, because the contract at stake is
    the wire outcome: with the ``TypeError`` arm gone the exception escapes
    ``_enforce_multipart_form_encoding`` -> ``_enforce_request_boundary`` -> ``run``
    and upstream's ``dispatch`` ``except HTTPException`` does not catch it, so a
    controlled ``400`` becomes an unhandled ``500``. That is not a claim a narrower
    row could not see the mutation - removing the arm makes the helper *raise*
    rather than return, so a row asserting only ``is False`` fails too. What this
    shape buys is that the assertions are the observable contract: the status code
    and the shared reason string, rather than a private helper's return value.
    """
    view = DjangoGraphQLView(schema=SCHEMA)

    with pytest.raises(HTTPException) as excinfo:
        view._enforce_multipart_form_encoding(_multipart_request(encoding=encoding))

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == _JSON_PARSE_REASON


def test_a_declared_utf8_charset_does_not_mask_a_middleware_set_request_encoding():
    """The two conditions are ``and``, not a fallback chain.

    The bypass this closes, proved end to end here rather than asserted: a client
    declares ``charset=utf-8``, one line of consumer middleware assigns
    ``request.encoding = "iso-8859-1"`` (Django's documented per-request
    override), and Django decodes every non-file field with the middleware's
    value - ``HttpRequest.parse_file_upload`` hands ``MultiPartParser`` only
    ``self.encoding`` and never re-reads ``content_params``. Resolving the gate as
    ``declared or request.encoding or DEFAULT_CHARSET`` therefore validated the
    value Django was NOT going to use, and let the *client* choose which rung was
    consulted.

    The second half is why the loss detector cannot be the backstop, and it is the
    reason this is a wire-contract defect rather than a cosmetic one: the same
    request, allowed to parse, decodes the raw Latin-1 byte cleanly into a
    different character with **no** replacement marker anywhere, so
    ``_reject_lossy_multipart_control_fields`` is structurally blind to it and a
    non-UTF-8-decoded control document would reach ``json.loads``. Asserting that
    here keeps the premise on disk: if a future Django started replacing instead,
    this row says so rather than silently becoming a tautology.
    """
    view = DjangoGraphQLView(schema=SCHEMA)
    latin1 = _multipart_body(b'{"query": "{ __typename }", "note": "\xe9"}')

    with pytest.raises(HTTPException) as excinfo:
        view._enforce_multipart_form_encoding(
            _multipart_request("utf-8", encoding="iso-8859-1", data=latin1),
        )

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == _JSON_PARSE_REASON

    unguarded = _multipart_request("utf-8", encoding="iso-8859-1", data=latin1)
    decoded = unguarded.POST["operations"]
    assert "\ufffd" not in decoded
    assert decoded == '{"query": "{ __typename }", "note": "\u00e9"}'
    assert json.loads(decoded)["note"] == "\u00e9"


_UNHONOURED_DECLARATIONS = (
    pytest.param("iso-8859-1", id="usable-name-django-promoted"),
    pytest.param("no-such-codec", id="unusable-name-django-dropped"),
)


@pytest.mark.parametrize("charset", _UNHONOURED_DECLARATIONS)
def test_a_declared_non_utf8_charset_is_refused_even_when_django_would_decode_utf8(charset):
    """The declared condition is independent, and this is the row that says so.

    Both requests here would be decoded as UTF-8 by Django - ``request.encoding``
    is UTF-8, which is the only value ``MultiPartParser`` receives - so the
    effective-encoding condition is satisfied and something else has to refuse
    them. That something is the declaration: a client asked for an encoding this
    endpoint will not honour, and accepting would mean honouring a declaration
    nobody honoured.

    Two shapes, because Django treats them differently and the package must not:
    a *usable* non-UTF-8 name is promoted onto ``request.encoding`` (so a
    middleware assignment is what puts UTF-8 back), while an *unusable* one is
    silently dropped and ``DEFAULT_CHARSET`` decides. The second is the shape that
    makes this condition strictly necessary rather than merely defensive - with it
    gone, ``charset=no-such-codec`` is accepted on any ordinary project.
    """
    view = DjangoGraphQLView(schema=SCHEMA)

    with pytest.raises(HTTPException) as excinfo:
        view._enforce_multipart_form_encoding(_multipart_request(charset, encoding="utf-8"))

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == _JSON_PARSE_REASON


def test_a_middleware_set_non_utf8_request_encoding_is_refused_on_its_own():
    """The effective-encoding condition's first sub-rung, with nothing declared.

    ``request.encoding`` is what ``parse_file_upload`` hands over, so a consumer
    middleware that sets it decides how ``operations`` is decoded without the
    request line changing at all. The control in the same row is what keeps this
    from passing for the wrong reason: the identical request with no declaration
    and no override is accepted, because ``DEFAULT_CHARSET`` is UTF-8.
    """
    view = DjangoGraphQLView(schema=SCHEMA)

    view._enforce_multipart_form_encoding(_multipart_request())

    with pytest.raises(HTTPException, match=_JSON_PARSE_REASON):
        view._enforce_multipart_form_encoding(_multipart_request(encoding="iso-8859-1"))


def test_a_reconfigured_default_charset_is_refused_but_a_declared_utf8_still_wins():
    """The effective-encoding condition's second sub-rung, and its exact boundary.

    ``MultiPartParser.__init__`` resolves ``encoding or
    settings.DEFAULT_CHARSET``, so a project that reconfigures ``DEFAULT_CHARSET``
    away from UTF-8 changes how every undeclared multipart form is decoded, and the
    endpoint's promise would quietly stop being true. It is refused instead.

    The second half is the part a "every rung must be UTF-8" reading gets wrong,
    and it is measured Django behavior rather than a preference: with
    ``DEFAULT_CHARSET`` set to Latin-1 and the client declaring ``charset=utf-8``,
    ``_set_content_type_params`` promotes ``utf-8`` onto ``request.encoding``,
    ``MultiPartParser`` receives ``utf-8``, and the form genuinely IS decoded as
    UTF-8 - so refusing it would be the package refusing a request Django handles
    exactly as the contract promises. The gate tracks what Django does, not a rung
    order of its own.
    """
    view = DjangoGraphQLView(schema=SCHEMA)

    with override_settings(DEFAULT_CHARSET="iso-8859-1"):
        with pytest.raises(HTTPException, match=_JSON_PARSE_REASON):
            view._enforce_multipart_form_encoding(_multipart_request())

        view._enforce_multipart_form_encoding(_multipart_request("utf-8"))


def test_a_get_carrying_a_stray_multipart_content_type_is_not_a_multipart_form():
    """The guard is scoped to the requests Django decodes.

    ``HttpRequest._load_post_and_files`` installs an empty ``QueryDict`` without
    parsing anything unless the method is ``POST``, so a stale
    ``multipart/form-data`` ``Content-Type`` on a GET describes a form that will
    never be decoded - and this endpoint reads no body on GET either. Refusing it
    was the package inventing a rejection for bytes nobody parses, and it made the
    mixin's own "**GET.** A no-op" sentence false.

    Asserted through ``_enforce_request_boundary`` rather than the encoding guard
    alone, because the claim is about the composed boundary: both halves have to
    be no-ops on this request, and the second half is what regressed.
    """
    view = _capped_view(_PROBE_CAP)

    view._enforce_request_boundary(_multipart_request("iso-8859-1", method="GET"))

    post = _multipart_request("iso-8859-1")
    with pytest.raises(HTTPException, match=_JSON_PARSE_REASON):
        view._enforce_request_boundary(post)


def test_a_non_multipart_request_is_not_subject_to_the_form_encoding_check():
    """The two declaration guards own disjoint request shapes.

    The multipart guard exists because Django decodes the control documents before
    the package sees them, using the value ``MultiPartParser`` receives - a question
    that only arises for a form. A JSON body never reaches that parser, so its
    declaration has its own owner,
    ``_enforce_body_charset_declaration``, and the same
    request must be refused by that one instead of by this one. Asserting both
    halves on the one request is what keeps the split from becoming a gap: either
    guard claiming both shapes, or neither claiming this one, fails here.
    """
    view = DjangoGraphQLView(schema=SCHEMA)
    request = RequestFactory().post(
        "/graphql/",
        data=b"{}",
        content_type="application/json; charset=iso-8859-1",
    )

    view._enforce_multipart_form_encoding(request)

    with pytest.raises(HTTPException, match=_JSON_PARSE_REASON):
        view._enforce_body_charset_declaration(request)


def test_a_multipart_declaration_is_left_to_the_form_encoding_guard():
    """The other direction of the same split, on a request both guards see.

    A multipart POST passes through both halves of the composed boundary, so the
    body-charset guard has to return without judging it - Django's own promotion
    rules and ``MultiPartParser``'s ``encoding or DEFAULT_CHARSET`` are what decide
    a form's encoding, and the multipart guard is written against exactly those.
    A second, coarser opinion here would refuse forms Django decodes precisely as
    the contract promises (a declared ``charset=utf-8`` under a Latin-1
    ``DEFAULT_CHARSET``, say).
    """
    view = _capped_view(_PROBE_CAP)

    view._enforce_request_boundary(_multipart_request("utf-8"))
    view._enforce_body_charset_declaration(_multipart_request("iso-8859-1"))


_DECLARED_JSON_CHARSETS = (
    pytest.param(None, 200, id="no-declaration"),
    pytest.param("utf-8", 200, id="utf-8"),
    pytest.param("UTF8", 200, id="alias-spelling"),
    pytest.param("iso-8859-1", 400, id="latin-1"),
    pytest.param("utf-8-sig", 400, id="utf-8-sig"),
    pytest.param("no-such-codec", 400, id="unknown-name"),
)

#: A JSON document whose bytes decode differently under the two codecs the rows
#: below declare: ``C3 A9`` is one character in UTF-8 and two in Latin-1. The
#: non-ASCII byte sits inside a GraphQL comment, so the document is a valid
#: operation whichever way an intermediary reads the rest of it.
_NON_ASCII_JSON_BODY = json.dumps(
    {"query": "{ ping } # \u00e9"},
    ensure_ascii=False,
).encode("utf-8")


async def _declared_json_response(charset, is_async):
    """POST the non-ASCII document with ``charset`` declared, over the real endpoint.

    The bytes go on the wire untouched, which is the only way to express the shape
    these rows are about - a declaration that contradicts the bytes it describes.
    ``generic`` is what does that: ``post`` re-encodes the payload with the charset
    it finds on the content type (and cannot even be handed a codec name Python
    does not know), while ``generic`` puts both the bytes and the header through
    unchanged.

    Driven through the whole handler rather than a view instance, so the assertions
    are the wire outcome an intermediary would see. The endpoint mounts live at the
    bottom of this module, which doubles as its own ``ROOT_URLCONF``.
    """
    content_type = "application/json"
    if charset is not None:
        content_type = f"{content_type}; charset={charset}"
    with override_settings(ROOT_URLCONF=__name__):
        if is_async:
            return await AsyncClient().generic(
                "POST",
                "/async-graphql/",
                data=_NON_ASCII_JSON_BODY,
                content_type=content_type,
            )
        return Client().generic(
            "POST",
            "/graphql/",
            data=_NON_ASCII_JSON_BODY,
            content_type=content_type,
        )


@pytest.mark.parametrize(("charset", "status"), _DECLARED_JSON_CHARSETS)
@pytest.mark.parametrize(
    "is_async",
    [pytest.param(False, id="sync"), pytest.param(True, id="async")],
)
async def test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with(
    is_async,
    charset,
    status,
):
    """A declared charset is part of the wire boundary, not decoration.

    The strict decode alone accepts ``Content-Type: application/json;
    charset=iso-8859-1`` for any body that happens to be valid UTF-8, and answers
    ``200``. The bytes then mean two different things at two hops: this endpoint
    reads ``C3 A9`` as one character, while a proxy, WAF, audit or signing layer
    that honours the declaration reads two - the same parser differential
    Decision 9's narrowing of the success set exists to remove, arriving through the
    header instead of through the body.

    So the declaration is refused rather than ignored, with the boundary's shared
    ``400``, and the rows cover exactly what "refused" means: absent is not a
    declaration and passes, every alias Python resolves to UTF-8 passes, and
    ``utf-8-sig`` - a different codec, whose BOM Decision 10 refuses - and an
    unknown codec name do not.

    Both transports run the same header-only check from the same
    ``_enforce_request_boundary``, and running the matrix twice is what keeps that
    structural claim honest end to end: an override or an ordering change reaching
    only one ``run`` would leave the other endpoint answering ``200`` for a
    declaration it does not honour. The accepted rows also assert the non-ASCII
    document really executed, rather than being quietly repaired into one that
    parses.
    """
    response = await _declared_json_response(charset, is_async)

    assert response.status_code == status
    if status == 200:
        assert json.loads(response.content)["data"] == {"ping": "pong"}
    else:
        assert response.content.decode() == _JSON_PARSE_REASON


def test_a_bytes_control_field_is_left_to_the_strict_decode_rather_than_the_marker_check():
    """A ``bytes`` value still carries its own encoding, so ``parse_json`` owns it.

    Unreachable from a live request - Django's multipart parser always hands over
    ``str`` - but the adapter protocol upstream's ``parse_multipart`` reads permits
    ``bytes``, and the two guards must not overlap: a marker check on undecoded
    bytes would be meaningless (no replacement has happened yet), while the strict
    decode is exactly the right owner. The lone ``0x80`` here is what that decode
    refuses, and this row pins that the marker check does not intercept it first.
    """
    view = DjangoGraphQLView(schema=SCHEMA)

    view._reject_lossy_multipart_control_fields({"operations": b'{"query": "\x80"}'})

    with pytest.raises(HTTPException, match=_JSON_PARSE_REASON):
        view.parse_json(b'{"query": "\x80"}')


# ---------------------------------------------------------------------------
# Ordering: the outer dispatch callback is ``csrf_exempt`` so
# Django's global ``CsrfViewMiddleware.process_view`` cannot read
# ``request.POST`` before the body boundary, and the view re-enters the same
# middleware from inside ``run``. The behavioral proof - a ``413`` with the
# upload-handler sentinel untouched, plus the full CSRF matrix on the requests
# that pass - is live in ``test_transport_api.py``; these two rows pin the
# mechanism that makes it possible.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark(view_class):
    """The mark has to be on the callback, and it has to come from ONE owner.

    ``CsrfViewMiddleware.process_view`` reads ``getattr(callback, "csrf_exempt")``,
    and the callback is the function ``as_view`` returns. A refactor that moved the
    mark somewhere ``process_view`` does not look would silently restore the
    ordering defect while every CSRF row stayed green, because the protection
    itself would still be enforced - twice - so the ordering has no other witness
    than this attribute and the live parser sentinel.

    The single owner is asserted too: both transports resolve ``as_view`` to the
    shared mixin, which is what makes it impossible for one of them to be exempt
    and the other not. And the marking must not cost the async transport its
    coroutine dispatch, so the async row re-asserts what
    ``test_async_view_as_view_is_marked_as_a_coroutine_function`` states - here in
    the presence of the wrapper that could have dropped it - along with the
    ``as_view`` bookkeeping ``functools.wraps`` carries through.
    """
    from django_strawberry_framework import views as views_module

    view = view_class.as_view(schema=SCHEMA)

    assert bool(view.csrf_exempt) is True
    assert getattr(view, _BOUNDARY_MARKER) is True
    assert view_class.as_view.__func__ is views_module._RequestBodyBoundaryMixin.as_view.__func__
    assert view.view_class is view_class
    assert view.view_initkwargs == {"schema": SCHEMA}
    assert iscoroutinefunction(view) is (view_class is AsyncDjangoGraphQLView)


def test_each_csrf_continuation_matches_the_transport_it_protects():
    """``csrf_protect`` branches on the callable it wraps, so the pair is not cosmetic.

    ``csrf_protect`` is ``decorator_from_middleware(CsrfViewMiddleware)``, and
    ``make_middleware_decorator`` chooses between an awaiting and a non-awaiting
    wrapper by asking ``iscoroutinefunction(view_func)``. If the async view's
    continuation were the sync function, the wrapper would hand a coroutine to
    ``process_response`` as if it were a response - so the async wrapper being a
    coroutine function IS the load-bearing fact, on the supported Django 5.2.0 floor
    as well as on current.

    Neither continuation may be ``csrf_exempt``: the exemption belongs to the outer
    callback alone, and one on the inner function would turn the re-entry into the
    bypass it must never be.
    """
    from django_strawberry_framework import views as views_module

    assert iscoroutinefunction(views_module._async_run_after_csrf_check)
    assert iscoroutinefunction(views_module._csrf_protected_async_run)
    assert iscoroutinefunction(views_module._csrf_protected_run) is False
    assert views_module._csrf_protected_run is not views_module._run_after_csrf_check
    for function in (
        views_module._run_after_csrf_check,
        views_module._async_run_after_csrf_check,
        views_module._csrf_protected_run,
        views_module._csrf_protected_async_run,
    ):
        assert getattr(function, "csrf_exempt", False) is False


# ---------------------------------------------------------------------------
# The ordering, supplied by the middleware chain instead of by the
# view: ``GraphQLRequestBodyBoundaryMiddleware`` runs the boundary from
# ``process_view`` and the exemption on the view callback withdraws itself, so the
# deployment's OWN ``CsrfViewMiddleware`` - base class or subclass - is what runs
# behind the boundary. These rows need a project whose ``MIDDLEWARE`` names a
# custom CSRF subclass and a URLconf that mounts the package views, which is a
# whole-chain shape fakeshop's single settings module cannot express, so the
# module doubles as its own ROOT_URLCONF.
# ---------------------------------------------------------------------------


class _RejectingCsrfMiddleware(CsrfViewMiddleware):
    """A project's own CSRF middleware: it records its calls and refuses the request.

    Stands in for the real thing a deployment installs - a subclass that binds the
    token to a session, adds a tenant check, or logs failures. Two behaviors, both
    load-bearing: recording proves whether Django's chain reached it at all, and
    rejecting proves its policy is what decides the response rather than merely
    running. Django's base implementation could prove neither, because a test client
    request passes its check and is indistinguishable from one it never saw.
    """

    calls: list[str] = []

    def process_view(
        self,
        request,
        callback,
        callback_args,
        callback_kwargs,
    ):
        """Apply the extra policy to exactly the callbacks the base class would check.

        The two deferrals are what make the recording meaningful rather than
        universal: a safe method is not something ``CsrfViewMiddleware`` checks, and
        an exempt callback is one it declines - so honouring both is what turns
        ``calls`` into evidence about whether Django's chain brought a *checkable*
        request here, which is the whole question these rows ask.
        """
        if request.method in (
            "GET",
            "HEAD",
            "OPTIONS",
            "TRACE",
        ) or getattr(
            callback,
            "csrf_exempt",
            False,
        ):
            return super().process_view(request, callback, callback_args, callback_kwargs)
        type(self).calls.append(request.path)
        return HttpResponseForbidden("the project's own CSRF policy refused this")


def _passthrough_middleware(get_response):
    """A function-style middleware, which the ordering check must skip rather than probe.

    ``settings.MIDDLEWARE`` admits any callable factory, so the ordering audit has
    to cope with an entry that is not a class at all - ``issubclass`` would raise
    ``TypeError`` on one.
    """
    return get_response


def _plain_view(request):
    """A non-package view, mounted so the middleware's pass-through is exercised."""
    return HttpResponse("plain")


_BOUNDARY_MIDDLEWARE_PATH = (
    "django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware"
)
_CSRF_MIDDLEWARE_PATH = "tests.test_views._RejectingCsrfMiddleware"
_PASSTHROUGH_MIDDLEWARE_PATH = "tests.test_views._passthrough_middleware"

_ORDERED_CHAIN = [_PASSTHROUGH_MIDDLEWARE_PATH, _BOUNDARY_MIDDLEWARE_PATH, _CSRF_MIDDLEWARE_PATH]

#: The mount cap the over-limit rows are refused by. Small enough that an ordinary
#: multipart envelope exceeds it, so the refusal is a property of the boundary
#: rather than of an enormous fixture.
_MOUNTED_CAP = 32

urlpatterns = [
    path("graphql/", DjangoGraphQLView.as_view(schema=SCHEMA)),
    path("async-graphql/", AsyncDjangoGraphQLView.as_view(schema=SCHEMA)),
    path(
        "capped/",
        DjangoGraphQLView.as_view(schema=SCHEMA, max_request_body_bytes=_MOUNTED_CAP),
    ),
    path(
        "async-capped/",
        AsyncDjangoGraphQLView.as_view(schema=SCHEMA, max_request_body_bytes=_MOUNTED_CAP),
    ),
    path("plain/", _plain_view),
]

_MOUNTED_PATHS = (
    pytest.param("/graphql/", "/capped/", False, id="sync"),
    pytest.param("/async-graphql/", "/async-capped/", True, id="async"),
)


@contextlib.contextmanager
def _chain(middleware):
    """This module as the project's URLconf, with ``middleware`` as the whole chain.

    ``ROOT_URLCONF`` points at this module because the rows' subject is Django's
    real request path through a chain: the view callback the URL resolver holds is
    what carries both ordering marks, and a ``RequestFactory`` call on a view
    instance would bypass every middleware hook that is being asserted.
    """
    _RejectingCsrfMiddleware.calls = []
    with override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=middleware):
        yield


async def _post(path, is_async, **kwargs):
    """POST through the real handler, on whichever client matches the transport."""
    if is_async:
        return await AsyncClient().post(path, **kwargs)
    return Client().post(path, **kwargs)


@pytest.mark.parametrize(("under", "over", "is_async"), _MOUNTED_PATHS)
async def test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read(
    under,
    over,
    is_async,
):
    """The invariant the middleware exists for: the boundary precedes the parse.

    ``CsrfViewMiddleware.process_view`` reads ``request.POST`` on every
    cookie-bearing POST, and on a multipart request that read IS the
    ``MultiPartParser`` invocation. With the boundary running from a middleware
    listed ahead of the CSRF entry, the ``413`` is produced before the CSRF
    middleware is entered at all - which is what the empty call log proves, and it
    is a stronger witness than an upload-handler sentinel because the class that
    would have parsed the body never ran.

    ``under`` is unused by this row and present only because both mounts come from
    one parametrization; the reason the over-limit mount is a separate URL is that
    the cap is a per-mount keyword.
    """
    with _chain(_ORDERED_CHAIN):
        response = await _post(over, is_async, data={"operations": "{}"})

    assert response.status_code == 413
    assert response.content.decode() == _BODY_LIMIT_REASON
    assert _RejectingCsrfMiddleware.calls == []


@pytest.mark.parametrize(("under", "over", "is_async"), _MOUNTED_PATHS)
async def test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering(
    under,
    over,
    is_async,
):
    """The defect this closes: a project's CSRF class must not be replaced here.

    Before the ordering moved into the chain, the package view marked its callback
    exempt and re-entered CSRF through ``csrf_protect``, which is built from
    Django's STOCK ``CsrfViewMiddleware``. A deployment whose ``MIDDLEWARE`` names a
    subclass - stronger token binding, a tenant check, failure logging - therefore
    had that subclass silently skipped on the GraphQL endpoint and the base
    implementation run in its place. No view-local decorator can fix that, because
    the configured class is a property of the chain.

    With the middleware installed the exemption withdraws itself, so the subclass
    runs on this endpoint exactly as on any other view: its ``process_view`` is
    called, and its refusal - not a package response - is what the client gets.
    """
    with _chain(_ORDERED_CHAIN):
        response = await _post(
            under,
            is_async,
            data=json.dumps({"query": "{ ping }"}),
            content_type="application/json",
        )

    assert response.status_code == 403
    assert _RejectingCsrfMiddleware.calls == [under]


@pytest.mark.parametrize(("under", "over", "is_async"), _MOUNTED_PATHS)
async def test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption(
    under,
    over,
    is_async,
):
    """Backward compatibility, asserted rather than assumed.

    A deployment that has not changed its ``MIDDLEWARE`` must behave exactly as it
    did: the callback stays exempt, so the project's CSRF middleware skips it -
    which the empty call log shows - the view enforces the boundary itself and then
    re-enters CSRF from inside ``run``, and both the allowed request and the
    over-limit one end where they always did. This is the row that would fail if the
    exemption had simply been deleted, or if the boundary had moved into the
    middleware and out of the view.
    """
    with _chain([_CSRF_MIDDLEWARE_PATH]):
        allowed = await _post(
            under,
            is_async,
            data=json.dumps({"query": "{ ping }"}),
            content_type="application/json",
        )
        refused = await _post(over, is_async, data={"operations": "{}"})

    assert json.loads(allowed.content)["data"] == {"ping": "pong"}
    assert refused.status_code == 413
    assert _RejectingCsrfMiddleware.calls == []


async def test_the_middleware_passes_a_non_package_view_through_untouched():
    """The marker is what scopes the middleware, so a foreign view costs one getattr.

    The middleware is a project-wide chain entry, and it holds no opinion about any
    view but the package's. Recognition is by the marker attribute
    ``_RequestBodyBoundaryMixin.as_view`` stamps rather than by an ``issubclass``
    check, which is also what keeps the dependency one-way: ``views.py`` imports the
    middleware module, never the reverse.
    """
    with _chain(_ORDERED_CHAIN):
        response = Client().get("/plain/")

    assert response.status_code == 200
    assert response.content == b"plain"


@pytest.mark.parametrize(("under", "over", "is_async"), _MOUNTED_PATHS)
async def test_the_view_does_not_measure_a_body_the_chain_already_measured(under, over, is_async):
    """One request, one measurement: the middleware stamps and the view believes it.

    The stamp is not an optimization detail - re-running the boundary would cost a
    second probe of a seekable stream or a second bounded read of bytes already
    proven to be within the limit, on every request the endpoint serves. The
    witness is the request object the view was handed: the mark is present, and the
    body it carries is still the client's, byte for byte, after passing through both
    owners.
    """
    seen = []
    body = json.dumps({"query": "{ ping }"}).encode()

    class _Recording(DjangoGraphQLView):
        def run(self, request, *args, **kwargs):
            seen.append((getattr(request, _BOUNDARY_ENFORCED, False), request.body))
            return super().run(request, *args, **kwargs)

    with _chain(_ORDERED_CHAIN):
        request = RequestFactory().generic(
            "POST",
            "/graphql/",
            data=body,
            content_type="application/json",
        )
        middleware = GraphQLRequestBodyBoundaryMiddleware(lambda _request: HttpResponse())
        view = _Recording.as_view(schema=SCHEMA)

        assert middleware.process_view(request, view, (), {}) is None
        view(request)

    assert seen == [(True, body)]


def test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup():
    """A chain that looks right and is not must fail loud, not fail silently.

    The whole guarantee is positional, and a deployment that appends the middleware
    to the end of ``MIDDLEWARE`` gets a chain where the CSRF read still precedes the
    boundary - with the exemption now withdrawn, so nothing catches it. That is
    exactly the state the middleware exists to leave behind, and it is invisible from
    the outside: every response looks correct until an oversized multipart request
    arrives and has already been parsed.

    So the audit runs where the chain is built, and the accepting rows are what keep
    it from being a blanket refusal: the documented order passes, a chain with no
    CSRF middleware at all passes (there is no read to precede, and the view's own
    continuation still protects the endpoint), and a function-style entry - which
    ``issubclass`` cannot be asked about - is skipped rather than probed.
    """
    with override_settings(MIDDLEWARE=[_CSRF_MIDDLEWARE_PATH, _BOUNDARY_MIDDLEWARE_PATH]):
        with pytest.raises(ConfigurationError, match="must appear BEFORE"):
            GraphQLRequestBodyBoundaryMiddleware(_plain_view)

    for chain in (
        _ORDERED_CHAIN,
        [_BOUNDARY_MIDDLEWARE_PATH, _PASSTHROUGH_MIDDLEWARE_PATH],
        [_CSRF_MIDDLEWARE_PATH],
    ):
        with override_settings(MIDDLEWARE=chain):
            assert GraphQLRequestBodyBoundaryMiddleware(_plain_view) is not None


async def test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call():
    """The mark is request-scoped on both chains, and a raising view does not leak it.

    The exemption's answer is read off a ``ContextVar``, because it has to be true
    for a package view mounted in a chain WITHOUT this middleware in the same
    process. Setting it around the downstream call is therefore only correct if it is
    also reset around it - and on the async chain the reset has to happen after the
    ``await``, which is the reason ``__acall__`` exists rather than a ``finally``
    wrapped around a returned coroutine.

    Both directions are asserted through the exemption object itself, which is the
    value ``CsrfViewMiddleware.process_view`` consults: false while a request is in
    flight, true again afterwards, including when the chain raised.
    """
    from django_strawberry_framework.middleware.request_body import _CSRF_ORDERING_EXEMPTION

    async def downstream(request):
        assert bool(_CSRF_ORDERING_EXEMPTION) is False
        raise RuntimeError("the downstream chain failed")

    middleware = GraphQLRequestBodyBoundaryMiddleware(downstream)

    assert iscoroutinefunction(middleware) is True
    with pytest.raises(RuntimeError, match="downstream chain"):
        await middleware(RequestFactory().get("/graphql/"))

    assert bool(_CSRF_ORDERING_EXEMPTION) is True
