"""Tests for the Strawberry request-body patch.

System-under-test: :mod:`django_strawberry_framework._strawberry_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The patch wraps :meth:`strawberry.http.base.BaseView.parse_json` to
enforce the package's UTF-8 wire contract and to close two upstream gaps
that otherwise surface as unhandled ``500``s:

1. The wrapper **owns** the request body's decode. A ``bytes`` body is
   decoded once with strict UTF-8 before the delegation (spec-065
   Decision 9), and a ``UnicodeDecodeError`` from that decode is
   translated into the same ``HTTPException(400, ...)`` Strawberry
   already raises for malformed JSON - it would otherwise escape
   upstream's ``except json.JSONDecodeError``, since
   ``UnicodeDecodeError`` is a ``ValueError`` and not a
   ``JSONDecodeError``. A ``str`` input (a GET query param, a multipart
   ``operations`` / ``map`` form field) is passed through untouched, so
   the delegate only ever sees ``str`` and ``json.loads``'s RFC 8259
   encoding auto-detection can no longer run: UTF-16 / UTF-32 (BOM or
   BOM-less) and a UTF-8 BOM are all rejected, with no branch written
   for any of them.
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

One attribution constraint shapes the wire-contract rows below: upstream
raises the byte-identical ``HTTPException(400, "Unable to parse request
body as JSON")`` for its own ``json.JSONDecodeError``, so **no test can
attribute a rejection by status or message**. Attribution is therefore
structural (which callable received what) or via ``__cause__``.
"""

import json
from unittest import mock

import pytest
from cross_web import HTTPException
from strawberry.http.base import BaseView

from django_strawberry_framework import _strawberry_patches as patches
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView


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
    """A non-UTF-8 body -> controlled ``HTTPException(400)``, not ``UnicodeDecodeError``.

    The raise now originates in the wrapper's own strict decode rather than
    inside the delegated ``json.loads`` (spec-065 Decision 9); the translation
    it lands in is the same one, which is why the contract added no ``except``
    clause, status code, or message.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), b'{"a":"\xff\xfe"}')
    assert excinfo.value.status_code == 400


def test_patched_parse_json_passes_through_valid_json():
    """The success path is untouched: valid UTF-8 JSON parses exactly as upstream.

    Both an ASCII body and a genuinely multi-byte one, because the wire
    contract narrowed the accepted set to UTF-8 and **not** to ASCII. The
    second body carries an e-acute (``C3 A9`` on the wire), so an ASCII-only
    decode would fail it.
    """
    assert patches._patched_parse_json(BaseView(), b'{"a": 1}') == {"a": 1}
    multibyte = json.dumps({"a": "caf\u00e9"}, ensure_ascii=False).encode("utf-8")
    assert max(multibyte) > 0x7F
    assert patches._patched_parse_json(BaseView(), multibyte) == {"a": "caf\u00e9"}


def test_patched_parse_json_hands_the_delegate_a_str_for_a_bytes_body():
    """Attribution (test-plan row 24): the decode happens here, not in ``json.loads``.

    Recording what the captured original actually receives is the crispest
    available proof, because a status-code or message assertion cannot
    distinguish the two mechanisms (see the module docstring). After the
    wrapper's decode the delegate sees a ``str`` equal to the body's UTF-8
    text, so upstream's ``json.loads`` never sees ``bytes`` again and its
    RFC 8259 encoding auto-detection is unreachable by construction.
    """
    seen = []

    def _recorder(view, data):
        seen.append(data)
        return {"recorded": True}

    with mock.patch.object(patches, "_original_parse_json", _recorder):
        assert patches._patched_parse_json(BaseView(), b'{"a": 1}') == {"recorded": True}

    assert seen == ['{"a": 1}']
    assert isinstance(seen[0], str)


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


@pytest.mark.parametrize(
    ("body", "cause"),
    [
        pytest.param('{"a": 1}'.encode("utf-16"), UnicodeDecodeError, id="utf-16-with-bom"),
        pytest.param('{"a": 1}'.encode("utf-32"), UnicodeDecodeError, id="utf-32-with-bom"),
        pytest.param(b'{"a": "\x80"}', UnicodeDecodeError, id="invalid-utf8-byte"),
        pytest.param(bytes(range(256)) * 4, UnicodeDecodeError, id="raw-binary"),
        pytest.param('{"a": 1}'.encode("utf-16-le"), json.JSONDecodeError, id="utf-16-le-no-bom"),
        pytest.param('{"a": 1}'.encode("utf-16-be"), json.JSONDecodeError, id="utf-16-be-no-bom"),
        pytest.param('{"a": 1}'.encode("utf-32-le"), json.JSONDecodeError, id="utf-32-le-no-bom"),
        pytest.param('{"a": 1}'.encode("utf-32-be"), json.JSONDecodeError, id="utf-32-be-no-bom"),
        pytest.param(b"\xef\xbb\xbf" + b'{"a": 1}', json.JSONDecodeError, id="utf-8-bom"),
    ],
)
def test_patched_parse_json_rejects_every_non_utf8_wire_shape(body, cause):
    """The wire matrix: every non-UTF-8 shape -> 400, and *which* mechanism refused it.

    The executable form of spec-065 Decision 9's measured-behavior table and of
    Decision 10 reason (a). The status and the message are identical across all
    nine rows - deliberately, so one byte sequence has one interpretation at
    every hop - so ``__cause__`` is the only thing that records the split:

    * ``UnicodeDecodeError`` - the wrapper's own strict decode refused the
      bytes (a BOM'd multi-byte form, an invalid byte, raw binary);
    * ``json.JSONDecodeError`` - the bytes decoded cleanly and upstream's own
      ``json.loads`` refused the resulting text (BOM-less multi-byte forms,
      and the UTF-8 BOM that Decision 10 declines to strip).

    Pinning the second group matters because that rejection is *inherited*: a
    future stdlib that tolerated a leading U+FEFF, or NUL-studded text, would
    silently turn these 400s into 200s with no package change to review.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), body)

    assert excinfo.value.status_code == 400
    assert excinfo.value.reason == "Unable to parse request body as JSON"
    assert type(excinfo.value.__cause__) is cause


def test_both_package_views_resolve_parse_json_to_the_one_patched_wrapper():
    """Sync/async parity is structural: one install site, no shadowing class.

    The behavioral colours live over real requests (sync in
    ``examples/fakeshop/test_query/test_products_api.py``, async in
    ``test_transport_api.py``). This row closes the regression channel those
    cannot see: an intermediate class - a future upstream ``GraphQLView``
    method, or a package override in ``views.py`` - defining ``parse_json`` on
    one transport only would silently un-patch that transport while every live
    row on the other stayed green. Asserting that ``BaseView`` is the sole MRO
    owner fails the moment such a class appears.
    """
    for view_class in (DjangoGraphQLView, AsyncDjangoGraphQLView):
        assert view_class.parse_json is patches._patched_parse_json
        owners = [klass for klass in view_class.__mro__ if "parse_json" in vars(klass)]
        assert owners == [BaseView]


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
