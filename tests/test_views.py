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
  three enforcement branches whose subject is view-internal state a wire
  response cannot show - that an over-limit *declaration* is refused without
  ``request._body`` ever being materialized, that a multipart request stays
  unmaterialized, and that GET is a no-op. Every request-shaped cap row (status
  codes, the reason on the wire, the parse / execution witnesses, the ASGI
  fragment shapes) is live in
  ``examples/fakeshop/test_query/test_transport_api.py``.

The schema is module-local and ORM-free: none of these contracts touches the
database, so no ``django_db`` marker and no registry mutation.
"""

import importlib
import sys

import pytest
import strawberry
from asgiref.sync import iscoroutinefunction
from cross_web import HTTPException
from django.test import RequestFactory, override_settings
from strawberry.django.views import AsyncGraphQLView, GraphQLView

import django_strawberry_framework
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.views import (
    _BODY_LIMIT_REASON,
    AsyncDjangoGraphQLView,
    DjangoGraphQLView,
    _declared_content_length,
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
    package view's ``__base__``: Slice 2 put ``_RequestBodyLimitMixin`` first in
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
    ``_RequestBodyLimitMixin`` (rather than on each view, or only handling it in
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


def test_a_declared_over_limit_request_is_refused_without_reading_the_body():
    """Decision 7 step 1: the declared gate rejects BEFORE ``request.body`` is touched.

    ``hasattr(request, "_body")`` is the load-bearing half. A ``413`` alone would
    be satisfied by an implementation that read and measured the whole payload
    first; the point of the declared gate is that an honestly-declared oversized
    request costs nothing to refuse. The under-limit control in the same test is
    what makes the negative witness meaningful - it shows ``_body`` DOES appear
    when the counted check has to run.
    """
    view = _capped_view(32)
    over = RequestFactory().post("/graphql/", data=b"x" * 4096, content_type="application/json")

    with pytest.raises(HTTPException) as excinfo:
        view._enforce_request_body_limit(over)

    assert excinfo.value.status_code == 413
    assert excinfo.value.reason == _BODY_LIMIT_REASON
    assert hasattr(over, "_body") is False

    under = RequestFactory().post("/graphql/", data=b"x" * 16, content_type="application/json")
    view._enforce_request_body_limit(under)
    assert hasattr(under, "_body") is True


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


def test_the_body_limit_mixin_stays_private_and_sits_first_in_both_base_lists():
    """The mixin is private, unexported, and ahead of upstream in the MRO.

    Ordering is load-bearing rather than stylistic: the mixin's ``run`` overrides
    live on the view classes themselves, but the class attribute and the shared
    enforcement method must resolve to the package's implementation rather than
    to anything upstream might later define under the same names. Being first is
    also what lets a consumer subclass override either half.
    """
    from django_strawberry_framework import views as views_module

    mixin = views_module._RequestBodyLimitMixin

    assert mixin.__name__ not in views_module.__all__
    assert DjangoGraphQLView.__bases__ == (mixin, GraphQLView)
    assert AsyncDjangoGraphQLView.__bases__ == (mixin, AsyncGraphQLView)
    assert DjangoGraphQLView.__mro__.index(mixin) < DjangoGraphQLView.__mro__.index(GraphQLView)
