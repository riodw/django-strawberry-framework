# DRY Review: `django_strawberry_framework/utils/` Before Spec 042

Definitive conclusion: the existing utility layer is already strong enough to
keep [`spec-042-debug_toolbar-0_0_14.md`][spec-042] small. The DRY risk is not
that the package lacks helpers; it is that the implementation could bypass the
helpers already present, or prematurely promote debug-toolbar-specific code into
`utils/` and make the package harder to reason about.

The highest-quality path is:

1. Reuse the existing generic primitives aggressively.
2. Promote only the response/view seams that are likely to be shared with the
   sibling response-extensions debug card.
3. Keep `django-debug-toolbar` imports inside the new middleware leaf, never in
   unconditional utility modules.

## Scope

Reviewed all existing `.py` files under [`django_strawberry_framework/utils/`][utils]:

- [`utils/imports.py`][utils-imports]
- [`utils/permissions.py`][utils-permissions]
- [`utils/querysets.py`][utils-querysets]
- [`utils/connections.py`][utils-connections]
- [`utils/input_values.py`][utils-input-values]
- [`utils/inputs.py`][utils-inputs]
- [`utils/converters.py`][utils-converters]
- [`utils/errors.py`][utils-errors]
- [`utils/write_values.py`][utils-write-values]
- [`utils/relations.py`][utils-relations]
- [`utils/strings.py`][utils-strings]
- [`utils/typing.py`][utils-typing]
- [`utils/__init__.py`][utils-init]

Also cross-checked major consumers in routers, DRF/form/model mutation code,
filters/orders, optimizer/connection code, and the new debug-toolbar spec.

## P1 Findings

### P1.1 - `require_debug_toolbar()` must be a thin `require_optional_module()` wrapper

[`utils/imports.py`][utils-imports] already owns the raising optional-dependency
primitive:

`django_strawberry_framework/utils/imports.py::require_optional_module`

The new middleware should not hand-roll:

```python
try:
    import debug_toolbar
except ImportError as exc:
    raise ImportError(_DEBUG_TOOLBAR_INSTALL_HINT) from exc
```

It should mirror [`routers.py`][routers] instead:

```python
from django_strawberry_framework.utils.imports import require_optional_module

_DEBUG_TOOLBAR_INSTALL_HINT = (
    "DebugToolbarMiddleware requires django-debug-toolbar, which is not installed. "
    "Install it with `pip install 'django-debug-toolbar>=7.0.0'`."
)


def require_debug_toolbar() -> Any:
    return require_optional_module("debug_toolbar", install_hint=_DEBUG_TOOLBAR_INSTALL_HINT)
```

That keeps all true-absence behavior on the one import primitive:

- no memoization, so eviction-simulated absence tests can re-hit the guard;
- original `ImportError` chained;
- feature-specific hint stays with the feature owner;
- no fourth import pattern.

Related cleanup: [`rest_framework/__init__.py`][drf-init] still hand-rolls the
same guard in `require_drf()`. That predates
`require_optional_module()`. A future DRY cleanup should change it to:

```python
def require_drf() -> Any:
    return require_optional_module("rest_framework", install_hint=_DRF_INSTALL_HINT)
```

That would align DRF, Channels, and debug toolbar under the same primitive.

### P1.2 - Do not put debug-toolbar imports or payload helpers in `utils/`

`django-debug-toolbar` is a soft dependency. Any helper that imports
`debug_toolbar.*` cannot live in [`utils/`][utils], because `utils` is imported by
hard-dependency code throughout the package.

Keep these local to the future middleware module:

- `_DEBUG_TOOLBAR_INSTALL_HINT`
- `require_debug_toolbar()`
- `_get_payload(toolbar)`
- `_HTML_TYPES`
- `DebugToolbarMiddleware`
- template path constants, if any

The payload helper is not a package-neutral utility. It reads
`DebugToolbar` panel objects, skips `TemplatesPanel`, and returns the
toolbar-specific `debugToolbar` shape. Moving it into `utils/` would make the
generic layer depend on an optional integration and would be the wrong
abstraction even if it reduces a few local lines.

### P1.3 - Extract a generic JSON-response rewrite helper only if spec 044 will repeat it

[`spec-042`][spec-042] requires `_postprocess()` to:

- decode a JSON response body;
- add a top-level `debugToolbar` key;
- re-encode with `DjangoJSONEncoder`;
- update `Content-Length` when present;
- leave streaming responses alone.

That is debug-toolbar-specific in purpose, but the mechanics are not. The
sibling response-extensions debug middleware is very likely to need the same
"mutate a JSON GraphQL response body and refresh headers" spine.

If spec 042 is implemented alone and no other module needs this yet, keep the
logic local for simplicity. If spec 044 is implemented soon or in the same arc,
create a neutral helper before the second copy lands, for example:

`django_strawberry_framework/utils/responses.py::rewrite_json_response`

Suggested contract:

```python
def rewrite_json_response(
    response: HttpResponse,
    mutator: Callable[[dict[str, Any]], bool | None],
    *,
    encoder: type[json.JSONEncoder] = DjangoJSONEncoder,
) -> bool:
    if response.streaming:
        return False
    if not response.get("Content-Type", "").startswith("application/json"):
        return False
    payload = json.loads(response.content.decode(response.charset))
    changed = mutator(payload)
    if changed is False:
        return False
    response.content = json.dumps(payload, cls=encoder).encode(response.charset)
    if response.has_header("Content-Length"):
        response["Content-Length"] = str(len(response.content))
    return True
```

Do not make this helper debug-toolbar-aware. It should know only HTTP response
mutation mechanics. The toolbar middleware supplies the mutator that injects
`debugToolbar`; the future response-extensions middleware supplies the mutator
that injects `extensions`.

### P1.4 - Centralize Strawberry-view detection if a second middleware needs it

The spec currently plans this local check:

```python
issubclass(view, strawberry.django.views.BaseView)
```

For spec 042 alone, a local two-line check is acceptable. If the sibling
response-extensions middleware or test client also needs to decide "is this a
Strawberry Django view?", create one neutral helper:

`django_strawberry_framework/utils/views.py::is_strawberry_django_view`

Suggested behavior:

```python
def is_strawberry_django_view(view: Any) -> bool:
    return isinstance(view, type) and issubclass(view, BaseView)
```

The helper should import Strawberry only. Strawberry is already a hard
dependency, so this is safe for `utils/`. It should not import
`django-debug-toolbar`, and it should not know about GraphiQL.

### P1.5 - Factor the soft-dependency absence fixture before a third copy lands

This is test DRY rather than package-source DRY, but it matters because spec 042
is explicitly adding a third soft dependency.

Two absence suites already carry similar machinery:

- [`tests/rest_framework/test_soft_dependency.py`][test-soft-dependency]
- [`tests/test_routers.py`][test-routers]

Spec 042 will otherwise copy the same pattern again:

- strict `sys.modules` eviction;
- `builtins.__import__` blocker;
- block only top-level optional-package imports;
- restore evicted modules;
- restore parent package attributes that may otherwise keep stale child module
  objects alive.

Before adding `tests/middleware/test_debug_toolbar.py`, create a test-only helper
module. Do not put this in package `utils/`; consumers should never import test
eviction machinery.

Suggested test helper surface:

```python
@contextmanager
def simulated_absent_package(
    monkeypatch,
    *,
    blocked_roots: tuple[str, ...],
    evict_prefixes: tuple[str, ...],
    parent_attrs: tuple[tuple[object, str], ...] = (),
):
    ...
```

Then DRF, Channels, and debug-toolbar absence tests can use one rigorously tested
eviction/restore discipline.

## P2 Findings

### P2.1 - Reuse `import_attr_if_importable()` for optional Postgres field imports

[`types/converters.py`][types-converters] currently has two near-identical
helpers:

- `django_strawberry_framework/types/converters.py::_resolve_array_field`
- `django_strawberry_framework/types/converters.py::_resolve_hstore_field`

Both are best-effort imports from `django.contrib.postgres.fields`. The generic
primitive already exists:

`django_strawberry_framework/utils/imports.py::import_attr_if_importable`

Replace the local helpers with:

```python
_ARRAY_FIELD_CLS = import_attr_if_importable("django.contrib.postgres.fields", "ArrayField")
_HSTORE_FIELD_CLS = import_attr_if_importable("django.contrib.postgres.fields", "HStoreField")
```

That keeps optional-import semantics in one module. It also improves failure
quality: an importable Postgres module missing the expected attribute is a broken
environment and should fail loud as `AttributeError`, not silently degrade.

### P2.2 - Decide whether the package wants one generic MRO-registry lookup

[`utils/converters.py`][utils-converters] owns
`convert_with_mro()`, which already centralizes the ordered-precheck plus MRO
walk plus raising fallthrough pattern for form and serializer converters.

The read-side converter still has local MRO registry walks:

- `django_strawberry_framework/types/converters.py::scalar_for_field`
- `django_strawberry_framework/types/converters.py::_field_output_type_for`

The current duplication is small and understandable. I would not contort the
read-side converter just to remove two loops. But the next time a third MRO
registry walk is added, either use `convert_with_mro()` directly or split out an
even smaller primitive:

`django_strawberry_framework/utils/converters.py::lookup_mro`

Suggested contract:

```python
def lookup_mro(value: Any, registry: Mapping[type, T], default: T | _Missing = _MISSING) -> T:
    for klass in type(value).__mro__:
        if klass in registry:
            return registry[klass]
    if default is not _MISSING:
        return default
    raise LookupError
```

Then `convert_with_mro()` can call `lookup_mro()`, and read-side output/scalar
lookups can share the same MRO semantics without inheriting converter-specific
precheck behavior.

### P2.3 - `request_from_info()` error text should mention Channels mapping contexts

[`utils/permissions.py`][utils-permissions] correctly supports three request
shapes in `request_from_info()`:

- `info.context.request`
- bare `HttpRequest`
- Strawberry Channels mapping context resolved through `ChannelsRequestAdapter`

The final error message still says only:

`Expected info.context.request or a bare HttpRequest.`

That is now incomplete. Update the message to include the mapping context:

```text
Expected `info.context.request`, a bare HttpRequest, or a Strawberry Channels
mapping context with `context["request"].consumer.scope`.
```

This is not just polish. Spec 042 and 044 are both observability/debugging work;
bad configuration errors need to point at the actual accepted shapes.

### P2.4 - Keep `request_from_info()` as the only request/context decoder

Do not add local request decoders in auth, response extensions, debug helpers,
test clients, or middleware-adjacent code.

Use `request_from_info()` whenever the call path starts from Strawberry `info`.
Do not use it in `DebugToolbarMiddleware.process_view()`: that path has a real
Django middleware `request`, not Strawberry `info`, so calling the helper there
would be an abstraction mismatch.

### P2.5 - Consider folding `FormInputFieldSpec` into `InputFieldSpec`

[`utils/inputs.py`][utils-inputs] defines the neutral write reverse-map
`InputFieldSpec`, while [`forms/converter.py`][forms-converter] still carries
`FormInputFieldSpec`.

The form spec is structurally close:

- `input_attr`
- `graphql_name`
- `form_field_name`
- `kind`

`InputFieldSpec` already has:

- `input_attr`
- `graphql_name`
- `target_name`
- `kind`
- optional serializer-only axes

The form flavor could use `target_name=form_field_name` and leave
`source`, `related_model`, and `nested_specs` as `None`. That would remove a
parallel dataclass and let form/serializer decoders share more reverse-map
terminology.

This is not required for spec 042, and I would not mix it into the middleware
commit. It is a legitimate future DRY cleanup if write-flavor internals are
touched again.

### P2.6 - Consider one conversion-result object if another converter family appears

[`forms/converter.py`][forms-converter] and
[`rest_framework/serializer_converter.py`][serializer-converter] both define a
conversion result with the same three slots:

- `annotation`
- `kind`
- `required`

Today the duplication is tolerable because each module owns different constants,
different extension APIs, and different error wording. If another field-converter
family lands, promote the structural shell to:

`django_strawberry_framework/utils/converters.py::FieldConversion`

Keep flavor-specific kind constants and error factories at the callers. Do not
promote this prematurely if only the existing two flavors need it.

### P2.7 - Preserve `iter_input_items()` and `iter_provided_input_fields()` as separate contracts

At first glance these two helpers look mergeable:

- `django_strawberry_framework/utils/input_values.py::iter_input_items`
- `django_strawberry_framework/utils/inputs.py::iter_provided_input_fields`

They are not the same contract.

`iter_input_items()` walks filter/order style input values and treats dicts and
dataclasses uniformly. It is used before family-specific normalization and
permission checks.

`iter_provided_input_fields()` walks Strawberry-generated write input classes via
`__strawberry_definition__.fields` and skips only `strawberry.UNSET`; explicit
`None` is still a provided value.

Do not collapse them. The DRY rule here is to keep the two names explicit so a
future write decoder does not accidentally import the filter/order active-input
rule and drop explicit nulls.

### P2.8 - Use `is_inactive_value()` everywhere filter/order input activity is tested

[`utils/input_values.py`][utils-input-values] owns the active-input rule:

`value is None or value is unset_sentinel`

New filter/order code should not write local variants like:

```python
if value in (None, UNSET):
    ...
```

or truthiness checks like:

```python
if not value:
    ...
```

Those would break valid falsy inputs such as `0`, `False`, and `""`. The existing
helper is intentionally identity-based.

### P2.9 - Keep connection pagination math single-sited

[`utils/connections.py`][utils-connections] is the right owner for all
connection-window contracts:

- sidecar kwarg names;
- sidecar presence;
- ambiguous empty window detection;
- `WindowRangePlan`;
- `derive_connection_window_bounds()`;
- `UnwindowableConnection`.

No debug-toolbar code should need this. But if debug output ever labels optimizer
pagination plans, it must read these helpers rather than re-deriving offset,
limit, reverse, marker-row, or total-count logic from resolver kwargs.

### P2.10 - Do not reimplement relation-cardinality classification

[`utils/relations.py`][utils-relations] owns:

- `relation_kind()`
- `is_many_side_relation_kind()`
- `is_forward_many_to_many()`
- `instance_accessor()`
- `has_composite_pk()`

Any future debug/inspection output that describes a Django relation should reuse
these helpers. In particular, do not key relation display or optimizer plan
explanations directly off `field.many_to_many` / `field.one_to_many` at a new
call site. Those branches are easy to get wrong for reverse FK and reverse
one-to-one fields.

### P2.11 - Use existing string helpers for GraphQL/Django name boundaries

[`utils/strings.py`][utils-strings] already owns:

- `snake_case()`
- `pascal_case()`
- `pascal_case_or_raise()`
- `graphql_camel_name()`

Spec 042 probably does not need name conversion. But test URLconfs, debug labels,
future response-extension payload keys, and any generated debug type names should
not introduce local regex or split/capitalize helpers. Use these functions unless
the desired casing is intentionally different.

### P2.12 - Use type-unwrapping helpers for any debug schema introspection

[`utils/typing.py`][utils-typing] owns Strawberry/Python/GraphQL unwrapping:

- `is_async_callable()`
- `unwrap_graphql_type()`
- `unwrap_return_type()`

Spec 042 middleware should not introspect schema return types. If the future
debug response extension inspects selected field types, it should not add another
`while hasattr(type_, "of_type")` loop. Use `unwrap_graphql_type()` for
graphql-core wrapper stacks and `unwrap_return_type()` for one list-wrapper layer.

### P2.13 - Keep mutation error envelopes on `utils/errors.py`

[`utils/errors.py`][utils-errors] owns the field-error leaf shape:

- `field_error()`
- `relation_field_error()`
- `validation_error_to_field_errors()`
- `join_error_path()`

Debug-toolbar middleware should not use these helpers; its failures are import
errors, middleware configuration errors, or upstream toolbar errors, not mutation
payload errors.

But any future write path must continue to terminate field-level errors through
`field_error()` and `relation_field_error()`. Do not create a second `FieldError`
constructor in auth/form/serializer/model code.

### P2.14 - Keep relation-id value checks on `utils/write_values.py`

[`utils/write_values.py`][utils-write-values] owns scalar write-value checks:

- `unencodable_text_error()`
- `raw_choice_value()`
- `coerce_relation_pk_or_none()`
- `type_check_relation_id()`

Spec 042 should not touch these. If any future debug/test helper creates write
inputs, it should use the public mutation paths rather than duplicating relation
id coercion or GlobalID model checks.

### P2.15 - Do not broaden `utils/__init__.py` casually

[`utils/__init__.py`][utils-init] intentionally re-exports only a small stable
subset. Most current package code imports from focused submodules, which makes
ownership obvious and avoids circular surprises.

For spec 042, import directly from the submodule:

```python
from django_strawberry_framework.utils.imports import require_optional_module
```

Do not add `require_optional_module`, `request_from_info`, or any new response
helpers to `utils/__init__.py` unless they are meant to become stable public-ish
utility exports.

## P3 Findings

### P3.1 - `convert_with_mro()` could accept `Sequence` or `Iterable`

`convert_with_mro()` currently accepts:

```python
isinstance_prechecks: list[tuple[type | tuple[type, ...], Callable[[Any], Any]]]
```

The implementation only iterates it. If a future caller wants a tuple constant,
the type annotation can widen to `Sequence[...]` or `Iterable[...]`. No behavior
change is needed now.

### P3.2 - `GeneratedInputArgumentsFactory._ensure_built()` uses `pending.pop(0)`

The BFS queue uses list `pop(0)`. For current filter/order graph sizes this is
fine. If generated input graphs become large, switch to `collections.deque` in
the utility base so both families inherit the improvement.

Do not make that change in spec 042; it is unrelated.

### P3.3 - `WindowRangePlan` is in the right module now

`WindowRangePlan` and `window_range_plan()` belong in
[`utils/connections.py`][utils-connections], not optimizer internals, because
the resolver and optimizer both depend on identical pagination math. Keep future
window/range additions there.

### P3.4 - The utility docstrings are verbose but useful

The utility package is heavily documented. That is appropriate because many
helpers encode cross-module correctness contracts, not convenience functions.

For new helpers, follow the existing docstring style:

- name the invariant the helper owns;
- name the caller-specific tail it deliberately does not own;
- explain why the helper lives in `utils/` and why it is cycle-safe;
- avoid copying spec prose that will become stale.

## Spec 042 DRY Checklist

Use this as the implementation gate before writing production code:

- `DebugToolbarMiddleware` lives in
  `django_strawberry_framework/middleware/debug_toolbar.py`, not in `utils/`.
- `require_debug_toolbar()` calls
  `utils/imports.py::require_optional_module`.
- No `importlib.import_module("debug_toolbar")` try/except is introduced.
- `django-debug-toolbar` imports happen only after the module-level guard.
- Package root import and `import django_strawberry_framework.middleware` remain
  toolbar-free.
- `_get_payload()` stays local unless another package module needs the same
  toolbar-panel payload.
- JSON response rewrite mechanics are promoted only if spec 044 would otherwise
  copy them.
- Strawberry-view detection is promoted only if a second module needs it.
- The test absence fixture is factored into test support before duplicating the
  DRF/Channels eviction machinery a third time.
- Middleware code never uses queryset visibility helpers. The toolbar observes
  the request; it should not participate in ORM planning or filtering.
- Middleware code never uses mutation `FieldError` helpers. Import/config errors
  should surface as `ImportError` or upstream middleware failures, not mutation
  payload envelopes.
- Test queries should keep using real fakeshop GraphQL requests per the spec,
  but generic GraphQL post/assert helpers should be shared if the same shape
  appears in multiple middleware/test-client suites.

## Module-by-Module Reuse Map

| Utility module | Existing owner contract | Spec 042 / future DRY guidance |
| --- | --- | --- |
| [`utils/imports.py`][utils-imports] | Optional import primitives: best-effort, loaded-only, and raising soft-dependency import. | Use for `require_debug_toolbar()`. Refactor DRF guard later. Use for Postgres field optional imports. |
| [`utils/permissions.py`][utils-permissions] | Request resolution and active input permission traversal. | Use `request_from_info()` only from Strawberry `info` paths, not Django middleware `request` paths. Update error wording for Channels mapping. |
| [`utils/querysets.py`][utils-querysets] | Query source normalization and `DjangoType.get_queryset` visibility routing. | Do not use in debug toolbar middleware. Use only if a future debug extension intentionally scopes querysets through normal resolver paths. |
| [`utils/connections.py`][utils-connections] | Relay connection window and sidecar contracts. | No spec-042 use. Future optimizer debug output must reuse these constants/plans instead of re-deriving pagination. |
| [`utils/input_values.py`][utils-input-values] | Filter/order dict/dataclass traversal and active-value rule. | No spec-042 use. Future filter/order debug code must reuse `iter_active_fields()` and `is_inactive_value()`. |
| [`utils/inputs.py`][utils-inputs] | Generated input class, namespace, build-cache, and write-input traversal substrate. | No spec-042 use. Future generated input work should use `make_input_namespace()`, `make_shape_build_cache()`, and `build_strawberry_input_class()`. |
| [`utils/converters.py`][utils-converters] | Converter dispatch skeleton. | Use if another converter family appears. Consider extracting `lookup_mro()` if read-side converter MRO loops multiply. |
| [`utils/errors.py`][utils-errors] | Mutation/write field-error leaves and validation mapping. | No spec-042 use. Keep all write envelope leaves here. |
| [`utils/write_values.py`][utils-write-values] | Write scalar/relation value coercion and validation. | No spec-042 use. Keep relation-id structural checks here. |
| [`utils/relations.py`][utils-relations] | Relation cardinality/accessor/composite-pk classification. | Future debug/inspection code should use these rather than direct Django flag checks. |
| [`utils/strings.py`][utils-strings] | GraphQL/Django casing helpers. | Use for any generated debug names or schema labels; do not add local casing helpers. |
| [`utils/typing.py`][utils-typing] | Async-callable and GraphQL/Strawberry type unwrapping. | Use for future debug schema introspection; do not add new `of_type` peel loops. |
| [`utils/__init__.py`][utils-init] | Narrow convenience re-export surface. | Prefer submodule imports. Do not add new exports unless intentionally stable. |

## Bottom Line

Spec 042 can be a very small implementation if it rides the current utility
layer:

- one soft-dependency wrapper over `require_optional_module()`;
- one middleware leaf with toolbar-specific imports and payload logic;
- one template;
- one rigorous test suite.

The only new generic package helper I would seriously consider in this arc is a
JSON-response rewrite helper, and only because the sibling response-extensions
debug middleware is likely to need the same response-body mutation mechanics.
Everything else either already exists in `utils/` or should stay local to the
debug-toolbar middleware.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-042]: spec-042-debug_toolbar-0_0_14.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[drf-init]: ../django_strawberry_framework/rest_framework/__init__.py
[forms-converter]: ../django_strawberry_framework/forms/converter.py
[routers]: ../django_strawberry_framework/routers.py
[serializer-converter]: ../django_strawberry_framework/rest_framework/serializer_converter.py
[types-converters]: ../django_strawberry_framework/types/converters.py
[utils]: ../django_strawberry_framework/utils
[utils-connections]: ../django_strawberry_framework/utils/connections.py
[utils-converters]: ../django_strawberry_framework/utils/converters.py
[utils-errors]: ../django_strawberry_framework/utils/errors.py
[utils-imports]: ../django_strawberry_framework/utils/imports.py
[utils-init]: ../django_strawberry_framework/utils/__init__.py
[utils-input-values]: ../django_strawberry_framework/utils/input_values.py
[utils-inputs]: ../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../django_strawberry_framework/utils/relations.py
[utils-strings]: ../django_strawberry_framework/utils/strings.py
[utils-typing]: ../django_strawberry_framework/utils/typing.py
[utils-write-values]: ../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-routers]: ../tests/test_routers.py
[test-soft-dependency]: ../tests/rest_framework/test_soft_dependency.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
