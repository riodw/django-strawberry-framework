"""Package-tier contracts for the package's Django GraphQL views (spec-065 Slice 1).

Deliberately narrow: this file holds only what a live request cannot express
(spec-065 Decision 13, Placement). Every request-shaped S1 proof - project
middleware, ``ALLOWED_HOSTS``, CSRF, security headers, cache policy, exact
routing, and the per-mount IDE / GET controls - is earned over fakeshop's real
``/graphql/`` in ``examples/fakeshop/test_query/test_transport_api.py``.

What stays here:

- the ``channels``-free import boundary (Decision 6 / Error shapes) - a proof
  about ABSENCE, which a live request cannot make;
- the ``as_view`` keyword surface, including the fact that Django's
  class-attribute guard is what admits or rejects a keyword (the constraint
  Slice 2's cap keyword satisfies with a class attribute on the mixin);
- the async twin's coroutine marking, pinned here so it does not depend on the
  live async probe surviving;
- Slice 2's body-cap knob: the ``max_request_body_bytes`` precedence ladder and
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
- Slice 3's strict UTF-8 wire contract, now that the package view owns it
  (spec-065 Decision 9): the per-encoding ``__cause__`` matrix, which is
  invisible over the wire because all nine rejected shapes carry the identical
  status and message by design.

The schema is module-local and ORM-free: none of these contracts touches the
database, so no ``django_db`` marker and no registry mutation.
"""

import contextlib
import importlib
import io
import json
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
from django.http import HttpRequest, RawPostDataException
from django.test import AsyncRequestFactory, RequestFactory, override_settings
from strawberry.django.views import AsyncGraphQLView, GraphQLView
from strawberry.http.base import BaseView

import django_strawberry_framework
from django_strawberry_framework import _cross_web_patches as cross_web_patches
from django_strawberry_framework import _strawberry_patches as patches
from django_strawberry_framework.exceptions import ConfigurationError
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
# changes (which Slice 2's mixin did); upstream's class identity is the thing
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
    package view's ``__base__``: Slice 2 put ``_RequestBodyBoundaryMixin`` first in
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
# Slice 2: the body cap's knob. The pure-function precedence + validation
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

    The two ``None``s mean different things by design (spec-065 Decision 7 step
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
    that cannot be misread. ``True`` is rejected explicitly because
    ``isinstance(True, int)`` is ``True`` and a boolean cap is always a mistake.
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
    separate concern (audit S4), already shielded by
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

    Ordering is load-bearing rather than stylistic: the mixin's ``run`` overrides
    live on the view classes themselves, but the class attribute, the shared
    enforcement method, and ``parse_json`` must resolve to the package's
    implementation rather than to anything upstream might later define under the
    same names. Being first is also what lets a consumer subclass override any
    part.
    """
    from django_strawberry_framework import views as views_module

    mixin = views_module._RequestBodyBoundaryMixin

    assert mixin.__name__ not in views_module.__all__
    assert DjangoGraphQLView.__bases__ == (mixin, GraphQLView)
    assert AsyncDjangoGraphQLView.__bases__ == (mixin, AsyncGraphQLView)
    assert DjangoGraphQLView.__mro__.index(mixin) < DjangoGraphQLView.__mro__.index(GraphQLView)


# ---------------------------------------------------------------------------
# Review Blocker 1: HOW the body is measured. A wire ``413`` cannot tell a
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
    """Review Blocker 1: the rejecting operation itself is bounded, not just the verdict.

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
    """A size probe may never answer "the body is empty" on its own (review W3-1).

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


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_stream_reporting_a_position_past_its_end_is_not_waved_through(view_class):
    """The other incoherent direction: a negative remaining count is not "empty".

    ``max(end - position, 0)`` clamped a negative measurement - a ``tell()`` that
    over-reports - to "no bytes remaining, allowed", so a full body reached
    ``HttpRequest.body`` unbounded. The pair is now judged instead of clamped, and
    the request falls through to the bounded read like any other stream the
    package cannot measure.

    What the fall-through can and cannot recover is worth stating, because this
    row pins it: the position the probe reported is a lie, so the restored
    position lands past the end and the request ends up with an **empty** body -
    a ``400`` at the parse, never a bypass. Recovering the true bytes is
    impossible once a stream misreports where it is, and rewinding to zero
    instead would corrupt a stream that was legitimately mid-position. The
    security property is what holds: the application never receives bytes the cap
    did not count. The two witnesses are that the probe's answer was NOT acted on
    (reads were attempted, the consumed stream was closed and replaced) - both
    absent in the clamping version, which returned before touching the stream.
    """
    view = _capped_view(_PROBE_CAP, view_class=view_class)
    stream = _OverReportingPositionStream(b"x" * (_PROBE_CAP * 16))
    request = _asgi_request(stream, None)

    view._enforce_request_body_limit(request)

    assert stream.requested != []
    assert stream.delivered == 0
    assert stream.closed is True
    assert hasattr(request, "_body") is False
    assert request.body == b""


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


@pytest.mark.parametrize("view_class", _VIEW_CLASSES)
def test_a_body_already_cached_by_middleware_is_measured_from_the_cache_and_refused(view_class):
    """The one shape the cap cannot bound, and the only thing left to do about it.

    ``CsrfViewMiddleware`` reads ``request.POST`` before the view runs, and for a
    ``application/x-www-form-urlencoded`` body that materializes ``_body`` through
    ``HttpRequest.body`` - an allocation that has already happened by the time
    ``run`` is entered and cannot be undone. The package must still refuse to
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
# Review High 2: the strict UTF-8 wire contract is the package VIEW's, so it
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

    The executable form of spec-065 Decision 9's measured-behavior table and of
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
    silently turn these 400s into 200s with no package change to review. Both
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
    """Review High 2: the identical nine rows with ``{"strawberry": False}`` in effect.

    This is the finding, executable. The strict decode used to live inside
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
    spec-065 Decision 9 passes them through untouched. Asserting object identity
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

    Identity with upstream's message is the contract (spec-065 Decision 9): a body
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
    """Review W3-2: the sync transport's body source is the package view's own.

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
