"""Tests for the Strawberry request-body patch.

System-under-test: :mod:`django_strawberry_framework._strawberry_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The patch wraps :meth:`strawberry.http.base.BaseView.parse_json` to
close two upstream gaps that otherwise surface as unhandled ``500``s:

1. ``json.loads`` on ``bytes`` raises ``UnicodeDecodeError`` when the
   bytes are not decodable under the encoding it detects, and that is a
   ``ValueError`` rather than a ``JSONDecodeError``, so it escapes
   upstream's ``except`` and becomes a ``500``. The wrapper translates it
   into the same ``HTTPException(400, ...)`` Strawberry already raises for
   malformed JSON.
2. A body that is not a GraphQL-over-HTTP envelope is rejected with
   ``HTTPException(400, ...)``: a top-level JSON *scalar*, or a JSON
   *array* containing any non-object element. Upstream's
   ``parse_http_body`` handles a JSON object and a JSON array of objects
   (batch) but lets a scalar fall through to ``data.get("query")`` and a
   non-object batch element fall through to ``item.get("query")`` -> raw
   ``AttributeError`` -> ``500``. A well-typed batch ``list`` (every
   element a ``dict``) is passed through so upstream's batch validation
   keeps ownership of enablement / size limits.

Because gap 2's scalar guard is a request-*body* contract enforced from
a generic JSON helper, ``apply()`` also installs
:func:`_patched_parse_query_params` - a source-pinned reimplementation
of ``BaseView.parse_query_params`` routing its two nested parses through
the captured original ``parse_json`` - so the guard never fires on
upstream's GET ``variables`` / ``extensions`` parses, where upstream has
its own precise per-param handling (``null`` -> ``None`` -> the request
executes; a scalar -> a per-param 400). The live GET regressions live in
``examples/fakeshop/test_query/test_products_api.py``; the tests here pin
the shield's parse semantics, the pair install lifecycle, and the
reimplementer's body pin.

**What is deliberately absent here.** The strict UTF-8 wire contract
(spec-065 Decision 9) used to live in this module and no longer does: it
is package *policy* with no upstream lifecycle, so gating it on
``APPLY_UPSTREAM_PATCHES`` meant a consumer disabling temporary
bug workarounds silently lost a security contract. It now belongs to
``views.py::_RequestBodyBoundaryMixin.parse_json``, and its rows - the
nine-shape encoding matrix, the ``__cause__`` attribution, the
patch-opted-out proof - live in ``tests/test_views.py``. This module's
rows therefore assert the *opposite* property on purpose: that upstream's
own ``bytes`` semantics survive here untouched, because that is what a
consumer mounting Strawberry's own view is entitled to.
"""

import json
from unittest import mock

import pytest
from cross_web import HTTPException
from strawberry.http.base import BaseView

from django_strawberry_framework import _strawberry_patches as patches


def test_apply_is_idempotent():
    """Repeated ``apply()`` calls leave the patch installed (self-healing no-op)."""
    patches.apply()
    patches.apply()
    assert patches._patch_is_installed() is True


def test_apply_reinstalls_when_method_reverted():
    """``apply()`` re-installs if a third party reverted ``BaseView.parse_json``."""
    patches.apply()
    assert patches._patch_is_installed() is True

    saved = BaseView.__dict__["parse_json"]
    try:
        BaseView.parse_json = patches._original_parse_json
        assert patches._patch_is_installed() is False

        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        BaseView.parse_json = saved


def test_patch_is_installed_on_base_view():
    """By the time pytest collects, ``AppConfig.ready()`` has installed both methods."""
    assert BaseView.__dict__["parse_json"] is patches._patched_parse_json
    assert BaseView.__dict__["parse_query_params"] is patches._patched_parse_query_params


def test_apply_reinstalls_pair_when_parse_query_params_reverted():
    """A partial revert (only ``parse_query_params``) makes ``apply()`` re-install the pair.

    ``_patch_is_installed()`` must report ``False`` when either method was
    reverted - the scalar guard must never run without its GET shield, so
    a half-installed state has to fall through to the install path.
    """
    patches.apply()
    assert patches._patch_is_installed() is True

    saved = BaseView.__dict__["parse_query_params"]
    try:
        BaseView.parse_query_params = patches._original_parse_query_params
        assert patches._patch_is_installed() is False

        patches.apply()
        assert patches._patch_is_installed() is True
        assert BaseView.__dict__["parse_query_params"] is patches._patched_parse_query_params
    finally:
        BaseView.parse_query_params = saved


def test_patched_parse_json_translates_unicode_decode_error():
    """An undecodable ``bytes`` body -> controlled ``400``, not a raw ``UnicodeDecodeError``.

    This is gap 1 in isolation, i.e. the state a consumer who mounts
    Strawberry's own view is in. The raise originates inside the delegated
    ``json.loads``: it detects UTF-8 for these bytes (they start with ``{``) and
    then fails to decode ``FF FE``, which upstream's ``except
    json.JSONDecodeError`` does not catch because ``UnicodeDecodeError`` is a
    ``ValueError`` instead. The reason is upstream's own, so the widened catch is
    indistinguishable from the catch it widens.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), b'{"a":"\xff\xfe"}')

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == patches._UPSTREAM_JSON_PARSE_REASON
    assert type(excinfo.value.__cause__) is UnicodeDecodeError


def test_patched_parse_json_passes_through_valid_json():
    """The success path is untouched: valid JSON parses exactly as upstream.

    Both an ASCII body and a genuinely multi-byte one (the second carries an
    e-acute, ``C3 A9`` on the wire). ``bytes`` are handed to the delegate
    unchanged - this wrapper does not decode - so what is asserted here is
    upstream's parse, not a package narrowing.
    """
    assert patches._patched_parse_json(BaseView(), b'{"a": 1}') == {"a": 1}
    multibyte = json.dumps({"a": "caf\u00e9"}, ensure_ascii=False).encode("utf-8")
    assert max(multibyte) > 0x7F
    assert patches._patched_parse_json(BaseView(), multibyte) == {"a": "caf\u00e9"}


@pytest.mark.parametrize(
    "encoding",
    [
        pytest.param("utf-16", id="utf-16-with-bom"),
        pytest.param("utf-16-le", id="utf-16-le-no-bom"),
        pytest.param("utf-32", id="utf-32-with-bom"),
        pytest.param("utf-8-sig", id="utf-8-bom"),
    ],
)
def test_patched_parse_json_leaves_upstreams_bytes_semantics_alone(encoding):
    """This wrapper does **not** narrow the accepted encodings, and must not start.

    The inverse of the view boundary's contract, asserted here so the ownership
    split cannot silently collapse back into one site. ``json.loads`` on ``bytes``
    performs RFC 8259 encoding auto-detection, which is documented upstream
    behavior rather than a defect, so a body that reaches *this* wrapper as bytes
    still parses. That is what a consumer who deliberately mounts
    ``strawberry.django.views.GraphQLView`` is entitled to.

    The rejection of these same four shapes is the package view's job
    (``tests/test_views.py``), and this row is what would fail if a future change
    put the strict decode back on the ``APPLY_UPSTREAM_PATCHES`` switch.
    """
    body = '{"a": 1}'.encode(encoding)

    assert patches._patched_parse_json(BaseView(), body) == {"a": 1}


def test_patched_parse_json_passes_a_str_body_through_without_reencoding():
    """A ``str`` input reaches the delegate as the **same object**, not a round trip.

    The GET query-param and multipart form-field paths arrive already decoded,
    and spec-065 Decision 9 passes them through untouched. Asserting object
    identity rather than equality is what rules out an incidental
    encode-then-decode cycle being introduced on those paths.
    """
    body = '{"a": 1}'
    seen = []

    def _recorder(view, data):
        seen.append(data)
        return {"recorded": True}

    with mock.patch.object(patches, "_original_parse_json", _recorder):
        patches._patched_parse_json(BaseView(), body)

    assert seen[0] is body


def test_patched_parse_json_passes_through_malformed_json_as_400():
    """Malformed (but UTF-8) JSON still becomes upstream's ``HTTPException(400)``.

    Pins that the wrapper does not regress Strawberry's existing
    ``json.JSONDecodeError -> 400`` handling - that error is raised by
    the delegated original and passes through the wrapper untouched.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), "{not valid json")
    assert excinfo.value.status_code == 400


@pytest.mark.parametrize(
    "body",
    [
        '"a string"',
        "42",
        "3.14",
        "true",
        "false",
        "null",
    ],
)
def test_patched_parse_json_rejects_non_object_body_as_400(body):
    """A valid-JSON scalar body -> ``HTTPException(400)``, not a passed-through scalar.

    Without the guard the scalar reaches ``parse_http_body``'s
    ``data.get("query")`` and raises a raw ``AttributeError`` -> ``500``.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), body)
    assert excinfo.value.status_code == 400


def test_patched_parse_json_passes_through_list_for_batch_handling():
    """A JSON array of objects passes through so upstream's batch validation owns it.

    The guard rejects scalars and lists with non-dict elements, but must NOT
    intercept a well-typed batch ``list`` - upstream's ``_validate_batch_request``
    is the path that accepts or rejects enablement / size limits.
    """
    assert patches._patched_parse_json(BaseView(), '[{"query": "{ x }"}]') == [
        {"query": "{ x }"},
    ]
    assert patches._patched_parse_json(BaseView(), "[]") == []


@pytest.mark.parametrize(
    "body",
    [
        "[1, 2, 3]",
        "[null]",
        '[{"query": "{ x }"}, 42]',
        '["not", "objects"]',
    ],
)
def test_patched_parse_json_rejects_batch_with_non_object_elements_as_400(body):
    """A JSON array containing any non-object -> ``HTTPException(400)``, not a pass-through.

    Upstream's ``_validate_batch_request`` never checks element types; with
    batching enabled the batch branch then does ``item.get("query")`` and
    raises a raw ``AttributeError`` -> ``500``. The envelope guard must reject
    those bodies before that path runs.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), body)
    assert excinfo.value.status_code == 400


@pytest.mark.parametrize("param", ["variables", "extensions"])
def test_patched_parse_query_params_parses_null_param_to_none(param):
    """A ``null`` query param parses to ``None`` - the scalar guard must not fire.

    ``None`` is a valid "object or null" value per upstream's own contract
    (``parse_http_body``'s per-param isinstance checks), so the shield must
    hand it through for the request to execute. An unshielded guard raised
    the request-body 400 here, regressing a previously-succeeding GET.
    """
    result = patches._patched_parse_query_params(
        BaseView(),
        {"query": "{ __typename }", param: "null"},
    )
    assert result[param] is None
    assert result["query"] == "{ __typename }"


def test_patched_parse_query_params_passes_scalar_through_for_upstream_handling():
    """A scalar param parses and passes through so upstream's per-param 400 owns it.

    ``parse_http_body`` raises the precise "`variables` must be an object or
    null, if provided." for a non-dict value; the shield must not shadow it
    with the guard's request-body message.
    """
    result = patches._patched_parse_query_params(
        BaseView(),
        {"query": "{ __typename }", "variables": "42"},
    )
    assert result["variables"] == 42


def test_patched_parse_query_params_parses_object_params():
    """The happy path: JSON-object params parse exactly as upstream."""
    result = patches._patched_parse_query_params(
        BaseView(),
        {"variables": '{"a": 1}', "extensions": '{"b": 2}'},
    )
    assert result["variables"] == {"a": 1}
    assert result["extensions"] == {"b": 2}


def test_patched_parse_query_params_malformed_param_is_upstream_400():
    """Malformed JSON in a param still becomes upstream's ``HTTPException(400)``.

    The error is raised inside the delegated original ``parse_json`` - the
    shield adds no error handling of its own.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_query_params(BaseView(), {"variables": "{not json"})
    assert excinfo.value.status_code == 400


def test_patched_parse_query_params_skips_empty_string_param():
    """An empty-string param is left unparsed - upstream's falsy skip, byte-for-byte."""
    result = patches._patched_parse_query_params(BaseView(), {"variables": ""})
    assert result["variables"] == ""


def test_patch_is_installed_false_when_base_view_symbol_missing():
    """``_patch_is_installed`` short-circuits to ``False`` when the symbol moved."""
    with mock.patch.object(patches, "BaseView", None):
        assert patches._patch_is_installed() is False


def test_apply_fails_loudly_when_symbols_missing():
    """A dependency-shape change cannot silently disable request hardening."""
    with mock.patch.object(patches, "BaseView", None):
        with pytest.raises(RuntimeError, match="BaseView.parse_json"):
            patches.apply()


def test_apply_fails_loudly_when_parse_json_signature_changes():
    """The patch pins the method arity it delegates to."""
    with mock.patch.object(patches, "_original_parse_json", lambda self: None):
        with pytest.raises(RuntimeError, match=r"expected \(self, data\) signature"):
            patches.apply()


def test_apply_fails_loudly_when_parse_query_params_missing():
    """A missing ``parse_query_params`` cannot silently strand the guard unshielded."""
    with mock.patch.object(patches, "_original_parse_query_params", None):
        with pytest.raises(RuntimeError, match="parse_query_params"):
            patches.apply()


def test_apply_fails_loudly_when_parse_query_params_signature_changes():
    """The shield pins the reimplemented method's arity."""
    with mock.patch.object(patches, "_original_parse_query_params", lambda self: None):
        with pytest.raises(RuntimeError, match=r"expected \(self, params\) signature"):
            patches.apply()


def test_apply_fails_loudly_when_parse_query_params_body_drifts():
    """A shape-passing but body-drifted upstream must not be silently superseded.

    The shield *reimplements* upstream's ``parse_query_params`` body, so
    validation pins the captured original's source, not just the
    ``(self, params)`` call shape (the ``_django_patches`` reimplementer
    precedent). A future strawberry that keeps the signature but changes
    the body - new query params, changed falsy-skip semantics - would
    otherwise pass validation and have its behavior replaced by a stale
    reimplementation. ``apply()`` must raise the targeted ``RuntimeError``
    before installing anything.
    """
    saved_parse_json = BaseView.__dict__["parse_json"]
    saved_parse_query_params = BaseView.__dict__["parse_query_params"]
    try:
        BaseView.parse_json = patches._original_parse_json
        BaseView.parse_query_params = patches._original_parse_query_params
        assert patches._patch_is_installed() is False

        def _drifted(self, params):
            """A (self, params)-shaped upstream whose body dropped the falsy skip."""
            params = dict(params)
            if "variables" in params:
                params["variables"] = self.parse_json(params["variables"])
            if "extensions" in params:
                params["extensions"] = self.parse_json(params["extensions"])
            return params

        with mock.patch.object(patches, "_original_parse_query_params", _drifted):
            with pytest.raises(RuntimeError, match="upstream body"):
                patches.apply()
        # ``apply()`` raised during validation, before the install step.
        assert patches._patch_is_installed() is False
    finally:
        BaseView.parse_json = saved_parse_json
        BaseView.parse_query_params = saved_parse_query_params


def test_apply_fails_loudly_when_parse_query_params_source_is_unavailable():
    """An unreadable captured original is treated as drift, not approved.

    ``inspect.getsource`` raises ``OSError`` for a function with no
    retrievable source file (built here via ``exec``, the shape a
    bytecode-only distribution would present). The validator must refuse
    to supersede a body it cannot verify.
    """
    namespace = {}
    exec("def _sourceless(self, params):\n    return dict(params)\n", namespace)

    with mock.patch.object(
        patches,
        "_original_parse_query_params",
        namespace["_sourceless"],
    ):
        with pytest.raises(RuntimeError, match="upstream body"):
            patches.apply()


def test_apply_no_ops_when_toggle_disabled(settings):
    """``APPLY_UPSTREAM_PATCHES = False`` makes ``apply()`` decline to install."""
    saved = BaseView.__dict__["parse_json"]
    try:
        BaseView.parse_json = patches._original_parse_json
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}
        patches.apply()
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": True}
        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        BaseView.parse_json = saved


def test_apply_no_ops_when_strawberry_dependency_opted_out(settings):
    """``{"strawberry": False}`` disables only this module; ``{"django": False}`` does not.

    The production half of the rev-apps.md Medium-2 scenario: opting out of
    the test-only Django patch alone leaves this request hardening
    installing normally (each gate reads its own dependency name).
    """
    saved_parse_json = BaseView.__dict__["parse_json"]
    saved_parse_query_params = BaseView.__dict__["parse_query_params"]
    try:
        BaseView.parse_json = patches._original_parse_json
        BaseView.parse_query_params = patches._original_parse_query_params
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"strawberry": False}}
        patches.apply()
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"django": False}}
        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        BaseView.parse_json = saved_parse_json
        BaseView.parse_query_params = saved_parse_query_params


def test_the_gated_workarounds_really_stop_hardening_when_opted_out(settings):
    """The opt-out is behavioral, not just an install flag - and stays that way.

    The companion to ``tests/test_views.py``'s patch-opted-out rows, and the
    reason both are needed: the wire contract must survive the switch, and the
    upstream-bug workarounds must not. If a future change moved the envelope
    guard or the ``UnicodeDecodeError`` translation somewhere ungated to make an
    opt-out row easier, this row fails - which is the point, because those two are
    workarounds for defects in a specific upstream version and a consumer pinning
    a fixed or reshaped Strawberry has to be able to turn them off.

    With the pair un-installed, upstream's own ``parse_json`` is what runs: a
    JSON scalar body parses straight through (it is the caller downstream, not
    this method, that then raises ``AttributeError``), and an undecodable body
    raises the raw ``UnicodeDecodeError`` upstream never catches.
    """
    saved_parse_json = BaseView.__dict__["parse_json"]
    saved_parse_query_params = BaseView.__dict__["parse_query_params"]
    try:
        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"strawberry": False}}
        BaseView.parse_json = patches._original_parse_json
        BaseView.parse_query_params = patches._original_parse_query_params
        patches.apply()
        assert patches._patch_is_installed() is False

        view = BaseView()
        assert view.parse_json("42") == 42
        assert view.parse_json("[1, 2, 3]") == [1, 2, 3]
        with pytest.raises(UnicodeDecodeError):
            view.parse_json(b'{"a":"\xff\xfe"}')
    finally:
        BaseView.parse_json = saved_parse_json
        BaseView.parse_query_params = saved_parse_query_params
