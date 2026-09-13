# Build: Escalation 043 / L2 — should `testing_endpoint_setting` validate its return?

Spec reference: `docs/SPECS/spec-043-test_client-0_0_14.md` Decision 7, `### Error shapes` (working-tree copy; dirty, rewrite intended)
Raised by: `docs/builder/bld-043-review-2-code_verification.md` finding **L2**, `### Notes for Worker 1` item 5
Subject: `django_strawberry_framework/conf.py::testing_endpoint_setting` (conf.py:503-515), consumer `django_strawberry_framework/testing/client.py::TestClient.__init__` (client.py:109)
Status: recommendation — maintainer decides

## Verdict in one paragraph

L2's premise is false. A non-`str` `TESTING_ENDPOINT` does **not** reach Django as a
bare `None`/`int`/`list` and fail opaquely: `django.test.RequestFactory.generic`
(and its async twin) coerces the path with `str()` before anything else
(`urlsplit(str(path))  # path can be lazy`, django/test/client.py:646 and :746 at
6.1; present in every cached release from the 5.2.0 floor to 6.1.0). `None` posts to
`/None`, `7` to `/7`, `["/graphql/"]` to `/['graphql/']`, and each produces the
**identical** failure a typo'd string does: a 404, then Django's
`ValueError: Content-Type header is "text/html; charset=utf-8", not "application/json"`,
with `WARNING django.request: Not Found: /None` in the captured log. So the
docstring's disputed sentence is TRUE for the value classes the reviewer named.
It is false for two other cases nobody named: `""` (a *string*, which routes to the
URLconf root and in fakeshop returns **200** HTML, not a 404), and a `str` subclass
whose `__str__` raises (fails inside Django's own `str(path)` with the consumer's
exception, a self-inflicted value). Recommendation: **restate the docstring (and the
two spec sentences that share its wording) to describe the real mechanism**; add
**no** validation. Rejecting non-`str` at the accessor would break a legitimate
spelling that works today, `TESTING_ENDPOINT = reverse_lazy("...")` (a `__proxy__`,
not a `str`), which is exactly the case Django's `str(path)` comment exists for.

## 1. What actually happens, per value class (executed, not reasoned)

Probe: `scratchpad/probe_endpoint.py` (fakeshop `config.test_settings`, real URLconf,
`django.test.Client`, `DJANGO_STRAWBERRY_KANBAN_DB` pointed at a scratch path that was
never created, so the shared `db.sqlite3` was not opened). Run with
`uv run python <scratchpad>/probe_endpoint.py`. Django 6.1, Python 3.14.2.

| `TESTING_ENDPOINT` value | accessor returns | Django log line | consumer sees | raised at |
|---|---|---|---|---|
| `None` | `None` (type `NoneType`) | `Not Found: /None` | `ValueError: Content-Type header is "text/html; charset=utf-8", not "application/json"` | `django/test/client.py::ClientMixin._parse_json` via `strawberry/test/client.py::_decode` via `client.py::TestClient._finish_response` (client.py:202) |
| `7` | `7` | `Not Found: /7` | same `ValueError` | same |
| `["/graphql/"]` | the list | `Not Found: /['graphql/']` | same `ValueError` | same |
| `b"/graphql/"` | the bytes | `Not Found: /b'graphql/'` | same `ValueError` | same |
| `""` | `""` | **no log line** (200, not a 404) | same `ValueError`; pytest frame locals show `response = <HttpResponse status_code=200, ...>` | same |
| `str` subclass, `__str__` raises, value `"/graphql/"` (correct path) | the subclass instance | none (never reaches routing) | `RuntimeError: hostile __str__ fired` | `django/test/client.py::RequestFactory.generic #"parsed = urlsplit(str(path))"` (client.py:646) |
| same subclass, value `"/nope/"` | same | none | same `RuntimeError` | same |
| `str` subclass, `__repr__` raises, `"/nope/"` | same | `Internal Server Error: /nope/` | `RuntimeError: hostile __repr__ fired` re-raised by the test client | `debug_toolbar/panels/settings.py::SettingsPanel.generate_stats` (`pformat` over every setting) — fakeshop's toolbar, not the package |
| control: `"/missing-graphql-endpoint/"` | the string | `Not Found: /missing-graphql-endpoint/` | same `ValueError` as row 1 | same as row 1 |
| `None` on `AsyncTestClient` | — | `Not Found: None` | same `ValueError` | `client.py::AsyncTestClient.query` (client.py:459) → `_finish_response` |
| `reverse_lazy("index")` (probe_lazy.py) | a `__proxy__`; `isinstance(_, str)` is `False` | routes: `HttpResponse 200 text/html` | works today | — |

What the consumer's **pytest report** shows for `None` (scratch test, `uv run pytest -n0
--no-cov -p no:cacheprovider --rootdir=. -c pytest.ini <scratchpad>/test_probe_report.py`):

```text
self = <django.test.client.Client object at 0x10c28ee40>
response = <HttpResponseNotFound status_code=404, "text/html; charset=utf-8">
...
E               ValueError: Content-Type header is "text/html; charset=utf-8", not "application/json"
.venv/lib/python3.14/site-packages/django/test/client.py:951: ValueError
------------------------------ Captured log call -------------------------------
WARNING  django.request:log.py:283 Not Found: /None
```

So under pytest the report names the status (frame locals, `--tb=long/auto` only), the
path as Django rendered it (`/None`, captured log), and the content type (the message).
Under plain `unittest` only the message survives; the status and path are not in the
exception text on any Django release (the `_parse_json` message is byte-identical in
every cached wheel, 4.2.25 through 6.1.0).

Floor check of the coercion that makes rows 1–4 behave: cached Django wheels in
`~/.cache/uv/archive-v0` grepped for `urlsplit(str(path))` in `django/test/client.py` —
5.2.0, 5.2.13, 5.2.14, 5.2.15, 5.2.16 (the `pyproject.toml` floor), 5.2.17, 6.0.0–6.0.8,
6.1.0: **2 sites each** (sync + async factory). 4.2.25 (below the floor) has 0 under that
spelling. Not every published 5.2.x point is in the cache; both ends and eleven interior
points are.

## 2. Accessor census — the whole module, derived from its own structure

Population: `rg -n '^[A-Z_]+_KEY\s*=' django_strawberry_framework/conf.py` → **10**
constants; one (`DJANGO_SETTINGS_KEY`) names the dict itself, **9** name a key.
`rg -n '^def ' conf.py` → 11 defs; minus `_normalize_user_settings` (dict guard) and
`reload_settings` (signal receiver) → **9 readers**, one per key. `rg -n 'getattr(settings,'`
→ 9 sites, matching. Every per-key reader is `getattr(settings, KEY, default)`.

| # | key / reader | validates in `conf.py`? | validated at consumer? | where |
|---|---|---|---|---|
| 1 | `APPLY_UPSTREAM_PATCHES` / `upstream_patches_enabled` | **yes** — bool-or-`Mapping[str,bool]` shape, key types, unknown names, `ConfigurationError` (conf.py:414-477) | n/a (four patch modules just call it) | the module's ONE in-accessor validator; justified in its docstring: four readers, one gate |
| 2 | `NESTED_CONNECTION_STRATEGY` / `nested_connection_strategy_setting` | no | **yes** | `optimizer/nested_fetch.py::resolve_strategy` (unknown name → `ConfigurationError`) |
| 3 | `SINGLE_PARENT_FAST_PATH` / `single_parent_fast_path_setting` | no | **no — by design** | `optimizer/single_parent_fetch.py #"if not single_parent_fast_path_setting()"`; pinned unvalidated by `tests/base/test_conf.py::test_single_parent_fast_path_setting_is_an_unvalidated_toggle` |
| 4 | `TESTING_ENDPOINT` / `testing_endpoint_setting` | no | **no** — Django's `str(path)` coerces | `testing/client.py::TestClient.__init__` |
| 5 | `HIDE_FLAT_FILTERS` / `hide_flat_filters_setting` | no | **no — by design** | `filters/inputs.py::_build_input_fields #"bool(hide_flat_filters_setting())"` |
| 6 | `RELAY_GLOBALID_STRATEGY` / `relay_globalid_strategy_setting` | no | **yes** | `types/relay.py::_validated_globalid_setting` (`ConfigurationError` naming the setting) |
| 7 | `MAX_REQUEST_BODY_BYTES` / `max_request_body_bytes_setting` | no | **yes** | `views.py::_resolved_max_request_body_bytes` (exact-`int` gate, `ConfigurationError`) |
| 8 | `RESOURCE_POLICY` / `resource_policy_setting` | no | **yes** | `utils/policies.py::resolve_policy` via `resource_policy.py::resolve_resource_policy` |
| 9 | `ERROR_POLICY` / `error_policy_setting` | no | **yes** | `utils/policies.py::resolve_policy` via `error_policy.py::resolve_error_policy` |

Tally: 8 of 9 are thin readers; 1 validates in the accessor. Of the 8 thin readers, 5 are
validated at their consumer and 3 are never validated anywhere. Decision 7's
"validation stays at the consumer" is the module's posture in fact, not just in
prose, and four sibling docstrings say so verbatim (`relay_globalid_strategy_setting`,
`max_request_body_bytes_setting`, `resource_policy_setting`, `error_policy_setting`:
"`conf.py` stays a thin reader"), as does `views.py::_resolved_max_request_body_bytes`
("Validation lives here rather than in `conf.py`, which stays a thin reader").

The decisive comparison is not the 5 validated-at-consumer keys but the 2 toggles
(#3, #5): their consumer's coercion (`bool()` / `if not`) IS the semantics, and the
repo pins that as a contract rather than a gap. The endpoint is the same shape with
Django's `str()` as the coercion. Row #1 is the only precedent for validating in
`conf.py`, and its docstring gives the DRY reason (four consumer modules, one gate);
the endpoint has one consumer.

## 3. Is there an existing seam a `str` gate would ride?

No. `_normalize_user_settings` validates the **dict**, not any key's value. Per-key
validation in this repo is either inline in `upstream_patches_enabled` (~60 lines:
defensive `dict()` copy, key-type guard, unknown-name guard, per-value type guard) or at
a consumer (`resolve_strategy`, `_validated_globalid_setting`,
`_resolved_max_request_body_bytes`, `resolve_policy`). The only shared "must be a
string" helper is `utils/strings.py::_plain_text`, whose message ("String helper input
must be a string") is for the naming helpers and would be a misuse here. A gate in the
accessor would reuse the *vocabulary* (`ConfigurationError`, `_safe_type_name`) but be a
**new mechanism**: the first scalar-setting type gate in `conf.py`.

It would also have to pick a shape, and neither choice is clean:

- `isinstance(value, str)` admits the hostile-`__str__` subclass (row 6 above still
  fails inside Django) and **rejects `reverse_lazy(...)`** (a `__proxy__`, `isinstance`
  → `False`, probe_lazy.py), which works today and is the case Django's own `# path can
  be lazy` exists for.
- `type(value) is str` (the `views.py` exact-type precedent) rejects both the hostile
  subclass and the lazy proxy, and also any benign `str` subclass.

Admitting lazies means `isinstance(value, (str, Promise))`, a Django-internal import into
`conf.py` for a test-only knob, to reject a class of values Django already coerces.

## 4. Who pays

The accessor has one consumer, `testing/client.py`, and the setting is read at
`TestClient` construction (and per `GraphQLTestMixin.query()`, which constructs one).
A malformed value fails the consumer's **first** test call, in their test run, never a
production request. What that run shows (section 1): the `ValueError` naming the
content type, the frame-local `HttpResponseNotFound status_code=404`, and the log line
`Not Found: /None` — which names the rendered wrong path. The failure the reviewer
described ("names neither the setting nor the endpoint") is not what happens; the
endpoint IS named, as Django rendered it. The Low grade is, if anything, generous to
the finding: nothing is wrongly permitted, and the observed failure is the same one a
typo'd string gets, which the spec already accepted as "the honest failure for a
transport-level misconfiguration".

## 5. Every clause of the docstring, checked

`conf.py::testing_endpoint_setting` docstring (conf.py:504-514):

| clause | status |
|---|---|
| "Reads `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]`, defaulting to `"/graphql/"` when the key (or the whole settings dict) is absent" | true (`test_setting_reader_helpers_default_and_override_values`, `test_delattr_clears_stale_cache_and_restores_defaults`) |
| "Consumed by `testing/client.py` at `TestClient` construction and per `GraphQLTestMixin.query()` call" | true (client.py:109; `GraphQLTestMixin.query` builds a `TestClient` per call) |
| "as the lowest rungs of the endpoint precedence ladder (per-call `url=` > constructor `path=` > class-attr `GRAPHQL_URL` > this setting > default)" | true (`tests/testing/test_client.py` rung tests) |
| "No validation beyond the shared malformed-dict guard" | true |
| "a wrong endpoint string surfaces as an ordinary 404 at request time" | **true for a non-root wrong string AND for `None`/`int`/`list`/`bytes`** (Django's `str()`); **false for `""`** (routes to the URLconf root — fakeshop: 200 HTML). The word "string" is narrower than the truth, not wider. |
| "where the failure names the actual response" | **partly true**: the `ValueError` names the response's `Content-Type`; the status appears only in pytest's frame-locals rendering; the path only in the captured `django.request` log. Under `unittest` neither status nor path is in the failure text. |

The same wording lives in the spec and the same grading applies:

- `docs/SPECS/spec-043-test_client-0_0_14.md:203-205` — "a wrong endpoint **value**
  surfaces as an ordinary 404 at request time": the most accurate of the three
  spellings (value, not string), modulo the `""` case.
- `spec:860-861` — "the endpoint accessor adds no validation of its own (a wrong
  *string* is a 404 at request time ...)": the italicised *string* implies non-strings
  behave differently; they do not.
- `spec:1198-1201` (Decision 7) — "a wrong endpoint string is an ordinary 404 at request
  time": same.
- `spec:851` (`### Error shapes`, non-JSON bullet) — "the traceback carries the failing
  status": **false on its own date**. Django's `_parse_json` message has never carried
  the status (identical text in every cached wheel, 4.2.25 → 6.1.0). The status is
  visible only because pytest prints the failing frame's locals under the default
  traceback style. Present at HEAD (`git show HEAD:… | rg 'carries the failing'` → line
  959) and in the working-tree rewrite (line 851); not a defect of today's rewrite.
- `client.py:176` `TestClient.query` docstring — "`ValueError` naming the non-JSON
  `Content-Type` of the 404/HTML body": accurate.
- `examples/fakeshop/test_query/test_client_api.py:133-145`
  `test_wrong_configured_endpoint_surfaces_django_non_json_decode_error` — pins the
  string case live; accurate.

## 6. Cost of each option

### A. Restate the docstring and the spec's matching sentences (recommended)

Not the reviewer's narrowing ("a wrong endpoint *string*"), which makes the sentence
LESS true (non-strings 404 too); a restatement of the mechanism. Proposed text for
`conf.py::testing_endpoint_setting`, last two sentences:

> No validation beyond the shared malformed-dict guard: the value is handed to
> `django.test.Client.post` unchanged, which coerces it with `str()` (so a
> `reverse_lazy()` works and a `None` posts to `/None`), and a wrong value surfaces at
> request time as whatever the URLconf serves at that path — ordinarily a 404 — via
> Django's non-JSON `ValueError` naming the response's `Content-Type`.

Edits implied (docstring/spec only, no behaviour change):

1. `django_strawberry_framework/conf.py::testing_endpoint_setting` docstring — the two
   sentences above.
2. `docs/SPECS/spec-043-test_client-0_0_14.md:1198-1201` (Decision 7) — "a wrong
   endpoint string is an ordinary 404" → "a wrong endpoint value (any type — Django's
   test client `str()`-coerces the path) is ordinarily a 404".
3. `spec:858-861` (`### Error shapes`, malformed-settings bullet) — drop the italicised
   *string* / "a wrong value is ordinarily a 404 at request time".
4. `spec:851` (`### Error shapes`, non-JSON bullet) — "the traceback carries the failing
   status" → "pytest's default traceback shows the failing `HttpResponse` (with its
   status) as a frame local of `_parse_json`, and the `django.request` log names the
   path; the exception message itself names only the `Content-Type`".
5. `spec:203-205` — already says "value"; leave, or add "(ordinarily)".

Tests: none **required** for a docstring change. Two rows are worth adding because they
make the restated claim mechanically failable (a future accessor gate flips them):

- Live (first home per AGENTS.md): parametrize
  `examples/fakeshop/test_query/test_client_api.py::test_wrong_configured_endpoint_surfaces_django_non_json_decode_error`
  over `"/missing-graphql-endpoint/"` and `None` — same `pytest.raises(ValueError,
  match="Content-Type.*text/html")`. Proves "non-`str` behaves like a wrong string"
  against the real URLconf.
- Package (`tests/base/test_conf.py`, the file that already pins this accessor and holds
  the exact precedent `test_single_parent_fast_path_setting_is_an_unvalidated_toggle`):
  one row asserting `testing_endpoint_setting()` returns a non-`str` verbatim,
  docstring stating why (Django coerces; a gate would reject `reverse_lazy`). `tests/base/`
  may grow rows, not files (AGENTS.md).

Rationale companion: none needed; Decision 7's alternatives list is untouched.

### B. Reject non-`str` at the accessor

Behaviour change plus a posture change. Edits implied:

1. `conf.py::testing_endpoint_setting` — a type gate raising `ConfigurationError` with
   `_safe_type_name`; must decide `isinstance` vs exact type vs `(str, Promise)` (section
   3); each choice either admits the hostile subclass, rejects `reverse_lazy`, or imports
   `django.utils.functional.Promise` into `conf.py`.
2. `tests/base/test_conf.py` — rows for `None`/`int`/`list` rejection, the message shape,
   and whichever subclass/lazy decision is taken (the `views.py` exact-int gate has the
   matching row pattern).
3. `spec:200-205` — "`ConfigurationError` — NOT used by this card (worth saying
   explicitly)" becomes false; rewrite.
4. `spec:239-245` (Slice 1 checklist) — "validation stays at the consumer" → rewrite.
5. `spec:1198-1201` (Decision 7) — rewrite the "No validation beyond" paragraph, and
   record the change in `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md`
   Decision 7 change record.
6. `spec:858-861` — new `### Error shapes` bullet for the rejection.
7. `## Test plan` and `## Definition of done` rows (five homes per contract).
8. Four sibling docstrings and `views.py::_resolved_max_request_body_bytes` say
   `conf.py` "stays a thin reader that does not validate"; after B that is true only
   for domain values, not shapes — each needs a qualifying clause or the claim rots.
9. `docs/README.md:514` (`APPEND_SLASH` note) and the glossary `TestClient` entry make
   no validation claim; unaffected.

Downstream break: `TESTING_ENDPOINT = reverse_lazy("graphql")` works today and would
raise `ConfigurationError` under `isinstance`/exact-type gates. No repo consumer spells
it that way, but graphene-django's `TESTING_ENDPOINT` (the knob's named lineage) is a
plain setting consumers routinely populate from `reverse_lazy`, and Django's test client
accepts lazy paths by design (`# path can be lazy` at the coercion site).

### C. Leave both as they are

Leaves a docstring that is false for `""` and a spec sentence ("the traceback carries the
failing status") that is false on its own date. The fix under A is five sentences and
no code; C has no cost advantage over A.

## Recommendation

**A.** Restate, do not gate. Strongest fact: Django's test client already coerces the
path with `str()` on every supported release, so the behaviour the reviewer wanted a
gate to produce (a non-`str` fails "naming the endpoint") already happens — the log
line is `Not Found: /None`, and the exception is the same one the spec chose as the
honest transport failure. The module's posture (8 of 9 readers thin; both toggles
deliberately unvalidated) and the `reverse_lazy` case both point the same way.

**Strongest counter-argument, stated fairly:** `Not Found: /None` is a clue, not a
diagnosis. A consumer who set `TESTING_ENDPOINT = None` meaning "use the default" gets
a 404 on a path spelled `/None`, has to notice the log line under `Captured log call`,
and has to infer that the package did not treat `None` as "unset" — where every other
package `None` seam (`DJANGO_STRAWBERRY_FRAMEWORK = None`, `Meta.optimizer_hints =
None`, `MAX_REQUEST_BODY_BYTES = None`) gives `None` a documented meaning. A
`ConfigurationError` reading "`TESTING_ENDPOINT` must be a str; got NoneType" is a
better first message, and the `reverse_lazy` objection is answerable with
`isinstance(value, (str, Promise))`. The reply is that this buys one clearer message for
a test-only knob at the price of the module's stated posture, five spec sites, a
Django-internal import into `conf.py`, and a new first-of-its-kind gate, for a failure
that already names the wrong path and fails the first test. If the maintainer weighs
the `None`-means-default confusion higher than that, B is coherent — but then it should
be spelled as "`None` falls through to the default" (a presence check, matching every
other `None` seam in the package), not as a type rejection.

## Not anticipated by the reviewer or the brief

- The reviewer's failure mode does not exist on any supported Django: `str(path)`
  coercion, 2 sites per release, 5.2.0 → 6.1.0.
- `""` is the one string that does NOT 404 (routes to the URLconf root; fakeshop serves
  200 HTML), so the "ordinary 404" clause is false for a *string*, not for the
  non-strings.
- `reverse_lazy()` is a working non-`str` endpoint value today; a `str` gate breaks it.
- `spec:851` "the traceback carries the failing status" was false when written: the
  status is a pytest frame-local artefact, never in Django's message.
- Fakeshop-only aside: the debug toolbar's `SettingsPanel` `pformat`s every setting on
  each toolbar-rendered response, so a settings value with a raising `__repr__` 500s
  the request before the package sees it (row 8 in section 1). Upstream toolbar
  behaviour under `INTERNAL_IPS`; not a package defect, recorded so nobody re-derives it.

## Instruments

- `scratchpad/probe_endpoint.py` (+ `.out`), `scratchpad/probe_lazy.py`,
  `scratchpad/test_probe_report.py` — session scratchpad, not in the repo.
- `uv run pytest -n0 tests/base/test_conf.py --no-cov` → 65 passed (working tree, today).
- Census greps quoted in section 2, populations stated.
- Django floor sweep over `~/.cache/uv/archive-v0/*/django/test/client.py`, versions read
  from each wheel's `django/__init__.py::VERSION`.
- HEAD vs working-tree comparison of the spec's three sentences via
  `git show HEAD:docs/SPECS/spec-043-test_client-0_0_14.md`: the "No validation beyond"
  paragraph, the malformed-settings bullet, and the "carries the failing status" clause
  are unchanged by today's rewrite.
