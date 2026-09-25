# Review · Comments: `django_strawberry_framework/utils/strings.py`

Status: verified
Run: 0.0.15 2026-09-24-1

## Trace

Read the whole target (7 docstrings, 1 inline comment block) and its test module
`tests/utils/test_strings.py`. One real caller per symbol, body read:
`snake_case` - `optimizer/walker.py::_resolve_selection_target` and
`optimizer/walker.py::_field_by_graphql_name` (the forward-name fallback), `types/base.py` field-map
build (grep); `pascal_case` - `types/converters.py` choice enum name,
`rest_framework/serializer_converter.py` enum name (grep); `pascal_case_or_raise` -
`sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` (passes whole `LOOKUP_SEP` paths),
`filters/inputs.py::_pascal_case`; `graphql_camel_name` - `utils/inputs.py` (owner re-export
comment), forms / rest_framework / mutations / filters / orders inputs (grep);
`flatten_lookup_path` - `utils/permissions.py`, `utils/inputs.py`, `orders/sets.py` (all three
mangles the docstring names); `_plain_text` - its twin `utils/imports.py::_plain_text`. Django
`Field._check_field_name` in `.venv` (E001 trailing `_`, E002 `__`, E003 `pk`; no case rule).

Instruments: `review_inspect.py` (census: every symbol has a docstring;
`<root>/comments/strings.json`); `build_tree_md.py --list-docstrings` on the target and on
`tests/utils/test_strings.py`: both `ok`, first lines rule-clean; `check_citations.py --paths
<target> --substrings --json`: 2 citations, both resolve (`<root>/comments/citations.json`);
provenance `rg`: 3 hits, all the example identifier `legacy` (rejected below).

Probes (workspace, cell default; no database reached, the target is pure `str -> str`, so
`sharded` / `pg` are inapplicable by construction):

- `review-20260925T033640-40b39b` (`<root>/comments/docstring_examples.py`): all 26 docstring
  examples hold; `snake_case(graphql_camel_name(n)) == n` for 8 edge names; `snake_case("A__xB")
  == "a_b"` (underscores consumed); runtime `snake_case.__doc__` is `_snake_case_cached`'s text,
  not the source docstring of `snake_case`.
- `review-20260925T033709-6ff984` (`<root>/comments/strawberry_reverse.py`): Strawberry
  `to_camel_case` then `snake_case` fails to round-trip `isbn_10` (`isbn10`), `is_a_b` (`isAB` ->
  `is_ab`), `_legacy_id` (`LegacyId` -> `legacy_id`).
- `review-20260925T033757-4a695a` (`<root>/comments/head_and_case.py`):
  `graphql_camel_name("Foo_bar") == "FooBar"` (head not lowercased); `pascal_case` and
  `graphql_camel_name` map `my_HTTP` and `my_http` to one name; a model field `myHTTP` passes
  `Model.check()` with no error.
- `review-20260925T033947-1047fd`: the F2 Proof line run now, prints `False False False True`.

Fingerprints: `django_strawberry_framework/utils/strings.py` 3ec3b262ea8666d4ba36cf83807ca377fee5a680;
`tests/utils/test_strings.py` 3dad1a9d42d88a061546f5ee11a37ca453436c4e;
`optimizer/walker.py` 611e8fae4985321c24f09ab4891e23079f7e1b18; `utils/__init__.py`
1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee; `utils/inputs.py`
ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0; `types/base.py` 91c587477ff8257e80dbb9a9c79859f34c5b4c7e;
`sets_mixins.py` ad8987ea2fb18bc9f2809ed3b203e87a78db5ba3; `filters/inputs.py`
82b52d97b8f8b26d2846df24dabcabb793507c87; `orders/sets.py` 6044ab1a11c77a42b715f0d0722fe7c9695064bc;
`utils/permissions.py` 9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec; `types/converters.py`
058f10813927c0691ba658d7d388820bd07cd52a; `rest_framework/serializer_converter.py`
6652d092544ebfc618ab1805d23e8c055c39c5d7; `utils/imports.py`
291ecedd30c7d8af9c007758112e867c09d031eb; `.venv/.../django/db/models/fields/__init__.py`
16f1071396d09ce9ae77fcf10de2b036ce4e6a41. (Package paths relative to `django_strawberry_framework/`.)

Proof prefix used below, `$P` (static, shared tree, no import):

```shell
P="import ast;t=ast.parse(open('django_strawberry_framework/utils/strings.py').read());D={n.name:ast.get_docstring(n) for n in t.body if isinstance(n,ast.FunctionDef)};D['<module>']=ast.get_docstring(t)"
```

## Findings

### High

None.

### Medium

#### F1 - module docstring describes a two-helper module (stale)

- **Observation** - `django_strawberry_framework/utils/strings.py` module docstring body. "Both
  directions" lists only `snake_case` and `pascal_case`; `graphql_camel_name` (the snake -> camel
  owner `utils/inputs.py` names this module for), `pascal_case_or_raise` and
  `flatten_lookup_path` are absent. It credits `snake_case` to "the optimizer (and any future
  resolver-side code)" while the `DjangoType` field maps (`types/base.py`, `types/finalizer.py`,
  `inspect_django_type`) key on it too. The closing paragraph uses "we'll", speculates about
  future styles, and its "a third style" premise is false: camel, Pascal, snake and flatten
  already live here.
- **Evidence** - caller grep in Trace; the first line itself is true and `--list-docstrings` ok.
- **Impact** - the module docstring is where a reader decides which helper owns a transform; it
  hides the camel owner, inviting an inline respelling.
- **Severity** - Medium: stale prose on a module every generated-input family imports.
- **Recommendation** - keep line 1 verbatim (no TREE.md change); replace the body with:

  ```text
  Every name transform the package applies at the GraphQL/Django boundary:

  - ``graphql_camel_name`` maps a Python attribute to the ``camelCase`` GraphQL
    name of a generated input field (filter, order, form, serializer and model
    mutation inputs), injective over lowercase snake-case identifiers.
  - ``snake_case`` maps a ``camelCase`` GraphQL name back to ``snake_case``; the
    optimizer walker and the ``DjangoType`` field maps use it to key Django
    field metadata by selection name.
  - ``pascal_case`` builds ``PascalCase`` type-name stems from field names and
    lookup paths (``<TypeName><FieldName>Enum`` choice enums, per-field filter
    and order input types); ``pascal_case_or_raise`` adds the guard against an
    empty stem.
  - ``flatten_lookup_path`` collapses a ``LOOKUP_SEP`` path into one identifier
    token.
  ```
- **Must not change** - n/a.
- **Proof** - `uv run python -c "$P;d=D['<module>'];print(all(s in d for s in ('graphql_camel_name','snake_case','pascal_case_or_raise','flatten_lookup_path')), \"we'll\" not in d, 'third style' not in d, d.splitlines()[0]=='GraphQL/Django naming helpers for case conversion and lookup-path flattening.')"`
  prints `True True True True` (now `False False False True`); `uv run python
  scripts/build_tree_md.py --list-docstrings django_strawberry_framework/utils/strings.py` prints
  `ok`; the verifier grades the body true against the callers in Trace.
- **Freshness** - see Trace fingerprints.
- Symbol: module; grade: stale; text before: the module docstring body after its first line; text after: above.

#### F2 - `snake_case` contract overclaims and lives on the private helper

- **Observation** - `django_strawberry_framework/utils/strings.py::_snake_case_cached` carries the
  public contract; `utils/strings.py::snake_case`'s own docstring ("Normalize ``name`` before
  consulting the bounded conversion cache.") is dead text, because `functools.wraps(...,
  assigned=("__module__", "__doc__", "__annotations__"))` overwrites it, so a source reader of the
  exported symbol never sees the contract. The contract text: (a) says reversing Strawberry's
  default converter "lets us look up the corresponding Django field name without an extra
  mapping"; false for digit-leading segments, adjacent one-letter segments and a leading
  underscore, which is why `optimizer/walker.py::_field_by_graphql_name` exists; (b) "existing
  underscores are preserved" is false for the `__x` marker (`"A__xB"` -> `"a_b"`); (c) "us".
- **Evidence** - runs `review-20260925T033640-40b39b` (runtime `__doc__`, marker) and
  `review-20260925T033709-6ff984` (three Strawberry names that do not round-trip).
- **Impact** - `snake_case` is in `utils.__all__`; a caller trusting (a) drops the forward-name
  fallback and silently loses fields such as `isbn10`.
- **Severity** - Medium: overclaimed contract on a public symbol; every documented example is
  correct and the one in-package caller already carries the fallback, so not High.
- **Recommendation** - move the contract onto `snake_case` and drop `"__doc__"` from `assigned`
  (keeps `__name__`, `__qualname__`, `__wrapped__`, cache controls); `_snake_case_cached` gets
  `"""Convert ``name`` to ``snake_case``; the memoized body behind ``snake_case``."""`.
  `snake_case` text after:

  ```text
  Convert a ``camelCase`` / ``PascalCase`` GraphQL name to ``snake_case``.

  Exact inverse of ``graphql_camel_name`` over lowercase snake-case
  identifiers, including leading, trailing and repeated underscores and the
  ``__x`` marker that function writes between adjacent one-letter segments
  (``"aA__xA"`` -> ``"a_a_a"``); that marker is the one place underscores are
  consumed rather than preserved.

  Strawberry's default ``to_camel_case`` names model fields and loses
  boundaries this cannot recover: a digit-leading segment (``isbn_10`` ->
  ``isbn10``), adjacent one-letter segments (``is_a_b`` -> ``isAB``) and a
  leading underscore (``_legacy_id`` -> ``LegacyId``). A caller that must
  resolve every selection also matches the forward name
  (``optimizer/walker.py::_field_by_graphql_name``).

  Acronym runs stay together and split before their final title-cased word
  (``"HTTPServer"`` -> ``"http_server"``); a digit attaches to the token
  before it (``"HTTPServer2API"`` -> ``"http_server2_api"``).

  ``name`` is normalized to an exact ``str`` before the bounded ``lru_cache``
  (2048 entries) is consulted: the walker reverses the same small vocabulary
  of schema field names on every request. ``cache_clear``, ``cache_info`` and
  ``cache_parameters`` are that cache's controls.

  Examples:
      ``"name"`` -> ``"name"``;
      ``"isPrivate"`` -> ``"is_private"``;
      ``"HTTPServer2API"`` -> ``"http_server2_api"``;
      ``"_legacyId"`` -> ``"_legacy_id"``.
  ```
- **Must not change** - `snake_case.__name__`, `__qualname__`, `__wrapped__`, `cache_*`
  attributes and every conversion result.
- **Proof** - `uv run python scripts/workspace.py run review/utils/strings.py/verify-comments-<n> -- python -c "import ast,inspect;from django_strawberry_framework.utils import strings as s;t=ast.parse(open(s.__file__).read());D={n.name:ast.get_docstring(n) for n in t.body if isinstance(n,ast.FunctionDef)};d=D['snake_case'];print(inspect.getdoc(s.snake_case)==d, len(D['_snake_case_cached'].splitlines())==1, all(x in d for x in ('isbn10','isAB','LegacyId','_field_by_graphql_name','__x')), ' us ' not in d)"`
  prints `True True True True` (now `False False False True`, run
  `review-20260925T033947-1047fd`); `uv run python scripts/workspace.py run
  review/utils/strings.py/verify-comments-<n> -- pytest
  tests/utils/test_strings.py::test_snake_case_preserves_lru_cache_controls --no-cov` passes.
- **Freshness** - see Trace fingerprints.
- Symbol: `snake_case`, `_snake_case_cached`; grade: stale (overclaim) + dead docstring; before /
  after: above.

#### F3 - `graphql_camel_name` first line claims a lowercase the body never does

- **Observation** - `django_strawberry_framework/utils/strings.py::graphql_camel_name` opens
  "Lowercase the head"; the body keeps `head` as written (`camel = head`). Also "``snake_case``
  reserves that marker when it precedes an uppercase segment" omits the other half of the rule:
  the marker must also follow an uppercase character (`"__xFoo"` stays literal, pinned by
  `tests/utils/test_strings.py::test_snake_case_distinguishes_x_token_from_adjacent_uppercase_escape`).
- **Evidence** - run `review-20260925T033757-4a695a`: `"Foo_bar"` -> `"FooBar"`.
- **Impact** - seven modules derive wire names through it; the first line is its contract.
- **Severity** - Medium: false statement of behavior on a package-public symbol (`strings.__all__`).
- **Recommendation** - first line: `Convert a snake-case Python attribute to its ``camelCase``
  GraphQL name (``galaxy_name`` -> ``galaxyName``).`; add `The head segment is kept as written;
  each later segment is ``str.capitalize``-d.`; marker sentence: `...``snake_case`` reads that
  marker as a separator only between two uppercase characters.` Rest unchanged.
- **Must not change** - n/a.
- **Proof** - `uv run python -c "$P;d=D['graphql_camel_name'];print('Lowercase the head' not in d)"`
  prints `True` (now `False`); verifier grades the docstring true against the probe above.
- **Freshness** - see Trace fingerprints.
- Symbol: `graphql_camel_name`; grade: stale; before / after: above.

#### F4 - `pascal_case` states false reasons

- **Observation** - `django_strawberry_framework/utils/strings.py::pascal_case`: (a) the acronym
  paragraph calls upper-case input "unreachable through the documented call chain (Django field
  names cannot contain upper-case characters)"; Django has no such rule and DRF serializer and
  filterset member names reach it too; (b) "Mirrors the analogous acronym caveat on
  ``snake_case``" points at a caveat `snake_case` does not state; (c) the interior-collapse
  paragraph gives `flatten_lookup_path` and Django's `__` ban as the reason, while
  `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` passes whole `LOOKUP_SEP` paths
  (`category__name` -> `CategoryName`) and relies on the collapse; (d) the first line says
  "Django field name", narrower than its callers.
- **Evidence** - run `review-20260925T033757-4a695a` (`myHTTP` passes `Model.check()`;
  `my_HTTP` / `my_http` share `MyHttp`); `Field._check_field_name` in `.venv` (E001-E003 only);
  `type_name_for` body.
- **Impact** - DRY principle 10: a wrong stated reason is worse than none; "unreachable" tells a
  maintainer not to worry about a case collision that a legal model reaches.
- **Severity** - Medium: false rationale on a public symbol (`utils.__all__`).
- **Recommendation** - first line: `Convert a ``snake_case`` field name or ``LOOKUP_SEP`` path to
  ``PascalCase``.`; interior paragraph: `Interior underscore runs collapse
  (``"double__underscore"`` -> ``"DoubleUnderscore"``), so a ``LOOKUP_SEP`` path PascalCases
  segment by segment (``"category__name"`` -> ``"CategoryName"``, the stem
  ``ClassBasedTypeNameMixin.type_name_for`` builds); the digit rule below pins the one interior
  boundary capitalization cannot encode.`; acronym paragraph: `Per-segment ``str.capitalize()``
  lower-cases every character after the first, so acronyms are not preserved
  (``"my_HTTP_response"`` -> ``"MyHttpResponse"``) and names differing only in letter case share
  a stem (``my_HTTP`` / ``my_http`` -> ``MyHttp``); Django and DRF accept upper-case field names,
  so the stem is injective only over lowercase input.` Edge, digit and empty paragraphs and the
  examples stay.
- **Must not change** - n/a.
- **Proof** - `uv run python -c "$P;d=D['pascal_case'];print('cannot contain' not in d, 'acronym caveat' not in d)"`
  prints `True True` (now `False False`); verifier grades every paragraph true against the probe
  and `type_name_for`.
- **Freshness** - see Trace fingerprints.
- Symbol: `pascal_case`; grade: stale (wrong stated reason); before / after: above.

#### F9 (verify 1) - `FieldMeta.name` documented as snake_case, the `field_map` key M1 made raw

- **Observation** - `django_strawberry_framework/optimizer/field_meta.py::FieldMeta` class
  docstring, `Attributes:` entry `name: The Django field name (snake_case).` The body stores
  `field.name` as declared (`FieldMeta.from_django_field` passes `field_name` through
  `_from_field_shape` unchanged), and after M1 that string is the key of
  `DjangoTypeDefinition.field_map` (`types/base.py::DjangoType.__init_subclass__` builds
  `{f.name: FieldMeta.from_django_field(f)}`), which may be mixed case (`isPublic`,
  `ownerRef`, `petItems` in the two new `tests/optimizer/test_extension.py` nodes). Routed by the
  Mechanics verifier; the gap names `from_django_field`, but the text sits on the class
  docstring (`from_django_field`'s own docstring says nothing about case).
- **Evidence** - body read; `rg -n "snake" optimizer/field_meta.py` = this one line; the two new
  nodes pass with mixed-case keys (Mechanics verification run `review-20260925T035700-1954d2`).
- **Impact** - "(snake_case)" on the attribute that is now the map key is the exact premise M1
  removed; a maintainer reading it would re-add `snake_case` keying and bring back the
  `FieldDoesNotExist` crash.
- **Severity** - Medium: stale comment on internal code (`FieldMeta` is not exported from the
  package root or `optimizer/__init__.py`) stating the contract a High fix changed.
- **Recommendation** - owner `optimizer/field_meta.py::FieldMeta`; rides on M1 (the item's
  contract change). Text after: `name: The Django field name as declared on the model
  (``field.name``, any letter case); the key of ``DjangoTypeDefinition.field_map``.`
  Module first line untouched, so no TREE.md render.
- **Must not change** - n/a.
- **Proof** - `rg -c "snake_case" django_strawberry_framework/optimizer/field_meta.py` prints
  nothing and exits 1 (now `1`); `rg -n "field_map" django_strawberry_framework/optimizer/field_meta.py`
  shows the `name:` entry; the verifier grades it true against `from_django_field` and
  `DjangoType.__init_subclass__`.
- **Freshness** - `optimizer/field_meta.py` 7215c887aa26; `types/base.py` 49057fad2058.
- Symbol: `FieldMeta` (attribute `name`); grade: stale.

### Low

#### F10 (verify 1) - `snake_case` gives "on every request" as the cache's reason

- **Observation** - `django_strawberry_framework/utils/strings.py::snake_case` (text landed from
  F2): "the walker reverses the same small vocabulary of schema field names on every request".
  The walker runs only on a plan build: a cross-request plan-cache hit in
  `optimizer/extension.py` (`self._plan_cache.get(cache_key)`) returns the cached plan without
  walking, so a repeated cacheable operation never calls `snake_case`.
- **Evidence** - `optimizer/extension.py` plan-cache read/insert region; the item's own
  `Path class:` line ("once per selection on every plan build (plan-cache miss, every
  non-cacheable request)").
- **Impact** - a stated reason for a design that overstates its frequency (REVIEW "Also": wrong
  stated reason); the reason itself (repeated vocabulary across plan builds) still holds.
- **Severity** - Low: bounded clarity; rides on `utils/strings.py`, which this item changes for
  F1-F4.
- **Recommendation** - replace "on every request" with "on every plan build (a plan-cache miss
  or an uncacheable operation)".
- **Must not change** - n/a.
- **Proof** - `uv run python -c "$P;d=D['snake_case'];print('every request' not in d, 'plan build' in d)"`
  prints `True True` (now `False False`).
- **Freshness** - `utils/strings.py` 536d175cd605; `optimizer/extension.py` e0e53a8e10fc.
- Symbol: `snake_case`; grade: stale (overclaimed reason).

#### F11 (verify 1) - broken `#"substring"` citation in a test the item touches

- **Observation** - `tests/optimizer/test_multi_db.py` module docstring cites
  `AGENTS.md #"Test through real usage and prefer the example project"`; AGENTS.md reads "Test
  through real usage, prefer the example project". Present at `ITEM_BASELINE`; the item touches
  this file for M1 (`_register_type_definition`).
- **Evidence** - `check_citations.py --paths <12 item paths> --substrings --json`
  (`<root>/verify-comments-1/citations.json`): 64 checked, 1 violation, this one.
- **Impact** - a dead pointer to the tier rule the docstring invokes (START.md "Source refs").
- **Severity** - Low: rides on a file changed for M1 (High).
- **Recommendation** - `AGENTS.md #"Test through real usage, prefer the example project"`; the
  quote stays on one source line.
- **Must not change** - n/a.
- **Proof** - `uv run python scripts/check_citations.py --paths tests/optimizer/test_multi_db.py --substrings`
  exits 0 (now 1, "1 unresolvable citation(s)").
- **Freshness** - `tests/optimizer/test_multi_db.py` 16753577c693.
- Symbol: module docstring; grade: stale (reference to text that no longer exists).

#### F5 - `_plain_text` omits its rejection contract

- **Observation** - `django_strawberry_framework/utils/strings.py::_plain_text` docstring says
  only "Normalize a string subclass"; the body also raises `ConfigurationError` for a non-string,
  the behavior `tests/utils/test_strings.py::test_string_helpers_reject_non_string_inputs` pins
  and the one that distinguishes it from its pass-through twin `utils/imports.py::_plain_text`.
- **Evidence** - bodies of both.
- **Impact** - a reader swapping one twin for the other changes the error contract unaware.
- **Severity** - Low: incomplete, not false, private.
- **Recommendation** - `"""Return ``value`` as an exact ``str``; raise ``ConfigurationError`` for
  a non-string.` + `A ``str`` subclass is copied through ``str.__str__`` so its overridden
  ``__hash__`` / ``split`` / ``replace`` never run inside these helpers or the ``lru_cache``."""`
- **Must not change** - n/a.
- **Proof** - `uv run python -c "$P;print('ConfigurationError' in D['_plain_text'])"` prints `True`
  (now `False`).
- **Freshness** - see Trace fingerprints.
- Symbol: `_plain_text`; grade: stale (incomplete); rides on F1-F4.

#### F6 - `pascal_case_or_raise` first line is not imperative

- **Observation** - `django_strawberry_framework/utils/strings.py::pascal_case_or_raise` opens
  "``pascal_case`` with the shared no-word-token guard." (a noun phrase; D401 unchecked, the
  reviewer is the gate).
- **Evidence** - REVIEW.md "Comments" first-line rule.
- **Impact** - clarity only.
- **Severity** - Low.
- **Recommendation** - first line `Return ``pascal_case(name)``, raising ``make_error(name)`` when
  it is empty.`; body unchanged.
- **Must not change** - n/a.
- **Proof** - `uv run python -c "$P;print(D['pascal_case_or_raise'].split()[0] in ('Return','Convert','Build'))"`
  prints `True` (now `False`).
- **Freshness** - see Trace fingerprints.
- Symbol: `pascal_case_or_raise`; grade: true body, first line off-rule; rides on F1-F4.

#### F7 - `flatten_lookup_path` carries a history count and misnames its transform

- **Observation** - `django_strawberry_framework/utils/strings.py::flatten_lookup_path`: "not four
  inline respellings" counts sites that no longer exist (process provenance; three mangles are
  named above it); "the prefetch ``to_attr`` escaping work exists" narrates work; "the
  ``.replace("__", "_")`` transform" understates the body, which loops until every run of two or
  more underscores is one (`"a____b"` -> `"a_b"`).
- **Evidence** - body; callers `utils/permissions.py`, `utils/inputs.py`, `orders/sets.py`.
- **Impact** - provenance in standing code (START.md "No process provenance").
- **Severity** - Low.
- **Recommendation** - body after the first line: ```` ``category__name`` -> ``category_name``:
  every run of two or more underscores becomes one. The one owner of this mangle behind (a)
  python-attr derivation for the generated filter / order input fields, (b) the
  ``check_<field>_permission`` method-name mangle, and (c) the order side's aggregate-alias
  mangle. ``LOOKUP_SEP`` must never survive into a generated attribute or alias: Django's
  ``prefetch_related`` / ``order_by`` machinery splits on it, the reason generated ``Prefetch``
  ``to_attr`` names escape it too. ````
- **Must not change** - n/a.
- **Proof** - `uv run python -c "$P;d=D['flatten_lookup_path'];print('four inline' not in d, 'escaping work' not in d)"`
  prints `True True` (now `False False`).
- **Freshness** - see Trace fingerprints.
- Symbol: `flatten_lookup_path`; grade: process provenance; rides on F1-F4.

#### F8 - provenance in the target's test module

- **Observation** - `tests/utils/test_strings.py::test_snake_case_preserves_lru_cache_controls`
  docstring says "historical cache-control surface"; the comment in
  `tests/utils/test_strings.py::test_pascal_case_handles_snake_case_inputs` narrates "Collapsing
  them made ... mint the same ... stem".
- **Evidence** - text.
- **Impact** - provenance in a test (START.md).
- **Severity** - Low.
- **Recommendation** - docstring `The normalization boundary keeps the ``lru_cache`` controls and
  the public name.`; comment `Leading / trailing underscore runs are preserved verbatim, the Pascal
  dual of ``graphql_camel_name``'s edge rule, so ``price`` / ``price_`` / ``_price`` members of one
  set mint distinct generated type-name stems (operator bag / range / enum).` Implemented only if
  Worker-2 touches this file for another finding; otherwise `deferred` (REVIEW.md "Severity").
- **Must not change** - n/a.
- **Proof** - `rg -c 'historical|Collapsing them made' tests/utils/test_strings.py` prints
  nothing and exits 1 (now `2`).
- **Freshness** - `tests/utils/test_strings.py` 3dad1a9d42d88a061546f5ee11a37ca453436c4e.
- Symbol: two test texts; grade: process provenance.

## Rejected

- Provenance `rg` hits `legacy` (3): the example identifier `_legacy_id`, not provenance. Reopen
  if a hit names a past design.
- Module first line: true, one sentence, `--list-docstrings` ok; no TREE.md edit owed. Reopen if
  the module gains a transform outside "case conversion and lookup-path flattening".
- Short-path citations `sets_mixins.py::...` / `filters/inputs.py::...` in
  `pascal_case_or_raise`: `check_citations.py` resolves each to one candidate. Reopen if a second
  same-named file makes either ambiguous.
- `pascal_case_or_raise` "both consumers": exactly two callers (grep). Reopen on a third.
- Inline `__x` comment in `_snake_case_cached`: true for every string `graphql_camel_name` emits
  from lowercase input.
- `pascal_case` edge / digit / empty paragraphs and all examples: true (run
  `review-20260925T033640-40b39b`).
- `tests/utils/test_strings.py` module docstring: both live-tier pointers hold
  (`test_schema_composition_api.py` introspects; `test_library_api.py` has 48 camel lookup names).
- Looks-for entries with no hit: public symbol without docstring (none); signature-restating
  docstring (none); "Tests that" / "Ensures" test docstrings (none); line-number references
  (none); unrecorded intentional separation: the `_plain_text` twins differ in contract, carried
  by F5 at this owner; whether one should absorb the other is Mechanics' call (Cross-axis there).

## Cross-axis (from Comments)

None placed here.

## Cross-axis (from mechanics)

- F1's proposed module text ("the optimizer walker and the ``DjangoType`` field maps use it to
  key Django field metadata by selection name") conflicts with Mechanics M1
  (`rev-utils__strings.mechanics.md`): M1 keys `DjangoTypeDefinition.field_map` by the raw
  Django name and removes `snake_case` from `types/base.py`, `types/finalizer.py` and
  `inspect_django_type.py`, leaving the walker's selection-name reversal (ahead of the forward
  fallback) as its only production use. The landed module text should describe that. M1 also
  makes stale `types/relations.py::PendingRelation`'s "snake-cased form used as a ``field_map``
  key" and the "already snake_cases the lookup side" sentence in
  `optimizer/walker.py::_resolve_field_map`; Worker-2 rewrites both under M1, and the Comments
  verifier grades them.
- F4 (a) agrees with M1's evidence: run `review-20260925T033713-1c7390` builds a model w/ field
  `isPublic` that Django accepts and the package finalizes.

Handoff: Two Mechanics leads sit in `rev-utils__strings.mechanics.md` `## Cross-axis (from
Comments)`: the `_plain_text` twin in `utils/imports.py` (reject vs pass-through), and the
letter-case collision of `pascal_case` / `graphql_camel_name` (`my_HTTP` vs `my_http`, both legal
Django names), which looks like a robustness row, not a defect, since no contract promises
case-injectivity. `utils/__init__.py` says ``strings`` is "case conversion (``snake_case``,
``pascal_case``)", the same two-helper framing as F1; it belongs to the `utils/` folder item,
out of this item's edit fence, so the folder's Comments pass should grade it. F2's text quotes
Strawberry's `to_camel_case` behavior at strawberry-graphql 0.324.0 (the copy's version); re-run
`strawberry_reverse.py` if the pin moves. Every Proof line was run before any edit and fails now
as recorded; the verifier should see each flip.

## Verification (Comments)

Verify pass 1, address `review/utils/strings.py/verify-comments-1`, copy synced fresh (run
`review-20260925T040338-49f937` header: package digest `sha256:a7408aee...c703e8`, = Worker-2's
"after" digest). Item diff `<root>/diff/pass-1.diff` blob `b8c938472fac`, 12 paths;
`git diff 6ac69870 -- <those 12>` hashes to the same blob, so the shared tree is exactly the
item diff. Proof lines run before reading `## Implementation (Worker-2)`.

Proof results:

- F1: `True True True True`; `--list-docstrings` `ok`. Landed. Body graded true against the
  callers (`rg` over the package: `graphql_camel_name` in forms / rest_framework / mutations /
  `utils/inputs.py` input builders; `snake_case` only in `optimizer/walker.py`, three sites, each
  with the forward fallback; `pascal_case` in the two enum-name sites and, through
  `pascal_case_or_raise`, `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` (filter and
  order per-field types) and `filters/inputs.py::_pascal_case`; `flatten_lookup_path` in
  `utils/permissions.py`, `utils/inputs.py`, `orders/sets.py`). The Cross-axis (from mechanics)
  adjustment landed: the `snake_case` bullet names the walker only.
- F2: `review-20260925T040338-49f937` prints `True True True True`;
  `test_snake_case_preserves_lru_cache_controls` passes (`review-20260925T040338-d751f4`).
  Landed. Worker-2's added boundary ("``isPublic`` stays ``isPublic``, which reverses to
  ``is_public``") is true (probe below). One phrase is not: F10.
- F3: `True`. Landed; head / capitalize sentence and "only between two uppercase characters"
  true (probe).
- F4: `True True`. Landed; interior paragraph true against `type_name_for`, acronym paragraph true
  (probe).
- F5: `True`. Landed; the added "exact-``str`` test runs first: it is every call the optimizer
  walker makes" is true by reading (the walker passes graphql-core selection names, exact `str`).
- F6: `True`. Landed.
- F7: `True True`. Landed; "every run of two or more underscores becomes one" true (probe).
- F8: prints `2`, unchanged. Worker-2 recorded it `deferred` (Low; `tests/utils/test_strings.py`
  is not in the item diff). Correct under REVIEW "Severity"; stays visible for `## Outcomes`.

Numbers reproduced: Worker-2's Comments claims are the Proof outputs above; all match.

Claim probe, `review-20260925T040528-3e127a` (`<root>/verify-comments-1/docstring_claims.py`, run
by absolute path in the copy): 18 claims from the landed `strings.py` docstrings, all hold
(round-trip over edge / repeated / marker / digit names, the four Strawberry-lossy boundaries
incl. `isPublic`, acronym and digit examples, `maxsize == 2048`, head kept as written, marker
literal after a lowercase, `category__name` -> `CategoryName`, `my_HTTP` / `my_http` ->
`MyHttp`, empty stems, flatten runs). Target is pure `str -> str`: sharded / pg inapplicable by
construction.

Whole-diff reading (prose diff: `review_changed_python_diffs_against_head.py 6ac69870 --against
worktree --prose --include-tests --include-init`, one `--path` per item path,
`<root>/verify-comments-1/diff/`); every docstring and comment Worker-2 wrote or moved:

- `optimizer/walker.py::_resolve_field_map` new sentence: true (both paths key by `f.name`;
  `_resolve_selection_target` reverses, checks connection slots, then `_field_by_graphql_name`).
- `types/__init__.py` dependency paragraph: true (`rg "snake_case\("` over `types/` = 0).
- `types/relations.py::PendingRelation`: true (raw name = map key after M1).
- `tests/types/test_finalizer.py::test_malformed_pending_field_name_is_rejected_before_relation_lookup`
  docstring: true, states the asserted behavior.
- `tests/optimizer/test_extension.py`: section banner, `_unmanaged_tables` and both new test
  docstrings true against their bodies and the walker path; the "no fakeshop model" sentence is
  a tier rationale, not provenance. `# noqa: N815` needed.
- Module first lines: no item path changed one (`--list-docstrings` on all 12: `ok`), so no
  TREE.md hunk is owed.
- Provenance / `we` / line-number sweep over the added prose: hits are the example identifier
  `legacy` and the word "cardinalities" only; no `we` / `us` / `you`, no `path:NN`.
- `check_citations.py --paths <12 paths> --substrings`: 64 checked, 1 unresolvable, pre-existing
  in `tests/optimizer/test_multi_db.py` (F11).

Attack: the other callers. `rg -i "snake.?case"` over the package outside `strings.py` finds one
stale sentence M1 left, outside the diff: F9 (the Mechanics verifier's routed gap; the text is on
the `FieldMeta` class docstring, not `from_django_field`). `utils/__init__.py`'s "case
conversion (``snake_case``, ``pascal_case``)" remains the `utils/` folder item's, as the review
handoff said.

Disputes: none recorded on Comments.

Cross-axis confirmations: the Mechanics record's reconstructed `## Cross-axis (from Comments)`
matches what this record's review handoff placed; wording confirmed. The Performance record's
`snake_case.__doc__` lead is discharged by F2.

Not graded as findings, with trigger: pre-existing past-tense narrative in
`tests/optimizer/test_walker.py` docstrings ("B2:", "Site 3 of the digit-boundary
reconciliation", "Gap 2a", "Before ... The walker now ...", "used to") in tests Worker-2 did not
edit. They describe the walker's forward resolution truly and are process provenance, owned by
the test module's own item (`optimizer/walker.py`, out of this run's scope). Reopens if this
item's revision edits one of those tests, or the walker item runs.

New findings: F9 (Medium), F10 (Low), F11 (Low), each labelled `verify 1` under `## Findings`
with a Proof line that fails now (run in the shared tree: `1`; `False False`; exit 1). F10 and
F11 ride on files this item already changes for higher findings.

Verdict: revision-needed. Gaps: F9, F10, F11 (runnable Proof lines above).

Fingerprints (12 chars): `utils/strings.py` 536d175cd605; `optimizer/field_meta.py`
7215c887aa26; `optimizer/walker.py` 73d6929a5881; `optimizer/extension.py` e0e53a8e10fc;
`types/relations.py` 4098eebca9b9; `types/__init__.py` 1bf69028dbdc; `sets_mixins.py`
ad8987ea2fb1; `tests/optimizer/test_extension.py` 4101bbd3805e; `tests/optimizer/test_multi_db.py`
16753577c693; `tests/optimizer/test_walker.py` 7a76159a24f6; `tests/types/test_finalizer.py`
05e1c9ecf621.

Handoff: Read beyond the record: the plan-cache read path in `optimizer/extension.py` (source of
F10), `FieldMeta.from_django_field` / `_from_field_shape` (name passes through unchanged),
`type_name_for`'s body, the walker's three `snake_case` sites. The next Comments verifier needs
only F9-F11's Proof lines plus a regrade of whatever prose the revision touches;
`optimizer/field_meta.py` enters the item diff with F9, so the diff has 13 paths. F9's text must
not reintroduce any case claim other than "as declared". `check_citations.py --substrings` on the
item paths is the instrument that found F11; rerun it on the revised diff. Probe source stays at
`<root>/verify-comments-1/docstring_claims.py`.

## Verification (Comments) pass 2

Address `review/utils/strings.py/verify-comments-2`, copy fresh (run
`review-20260925T041217-b0a2ef`: digest `sha256:ffacb690...b08dcb`, shared tree unmoved since
sync). Item diff `<root>/diff/pass-2.diff` blob ba49cf9b2818, 13 paths;
`git diff 6ac69870 -- <those 13>` is byte-identical (`cmp`), so the shared tree is exactly the
item diff. `diff pass-1.diff pass-2.diff`: three new hunks (the `FieldMeta` `name:` entry, the
`snake_case` cache-reason sentence, the `test_multi_db.py` citation) plus hunk-header offsets;
nothing else moved. Proof lines run before reading `## Iterations` / Implement pass 2.

Proof results (every line in the record):

- F1: `True True True True`; `--list-docstrings` `ok`.
- F2: `review-20260925T041217-b0a2ef` prints `True True True True`;
  `test_snake_case_preserves_lru_cache_controls` 1 passed (`review-20260925T041222-44f427`).
- F3 `True`; F4 `True True`; F5 `True`; F6 `True`; F7 `True True`: pass-1 results hold.
- F8: `2`, still `deferred` (test file outside the item diff). Correct under REVIEW "Severity".
- F9: `rg -c snake_case optimizer/field_meta.py` prints nothing, exit 1; `rg -n field_map` shows
  the `name:` entry (line 65). Landed.
- F10: `True True`. Landed.
- F11: `check_citations.py --paths tests/optimizer/test_multi_db.py --substrings` exit 0, "4
  citations resolve". Landed.

Numbers reproduced: Worker-2's pass-2 claims are these Proof outputs plus "66 resolve, 0
unresolvable" over the 13 paths, reproduced (`<root>/verify-comments-2/citations.json`: checked 66,
violations 0).

Grades of the three landed texts:

- `optimizer/field_meta.py::FieldMeta` `name:` - true. `from_django_field` passes `field.name`
  through `_from_field_shape` unchanged; both map builders, `types/base.py::DjangoType.__init_subclass__`
  and the walker's unregistered fallback (`optimizer/walker.py`, `{f.name: FieldMeta.from_django_field(f)
  ...}` over `model._meta.get_fields()`), key on it. No case claim beyond "as declared".
- `utils/strings.py::snake_case` cache sentence - true. The three `snake_case` sites
  (`_resolve_selection_target`, `_walk_selections`, `_selected_scalar_names`) are all reached only
  inside a walk; the sole production `plan_optimizations` caller is
  `optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan`, which walks after a
  `_plan_cache` miss and, for an uncacheable plan, after an `exec_memo` miss, storing it there so
  the walk runs once per execution per key. Worker-2's "uncacheable plan once per execution" is
  more exact than the record's "uncacheable operation".
- `tests/optimizer/test_multi_db.py` module docstring citation - true; quote matches AGENTS.md
  rule 10 on one line. The line is 121 chars; `tests/**` ignores E501, `ruff check` passes.

Whole-diff reading: prose diff regenerated (`review_changed_python_diffs_against_head.py 6ac69870
--against worktree --prose --include-tests --include-init`, 13 `--path`s,
`<root>/verify-comments-2/diff/`). Only the three hunks above are new since pass 1; pass-1 grades
stand for the rest. Sweep of all 254 added prose lines (`<root>/verify-comments-2/added_prose.txt`)
for `we` / `us` / `you`, provenance vocabulary and `.py:NN`: 3 hits, all the example identifier
`_legacy_id`. `--list-docstrings` on the 13 paths: 13 ok, no first line changed, TREE.md owes
nothing (`git diff 6ac69870 -- docs/TREE.md` empty).

Inverse proof, independent of Worker-2's: pass-1 versions rebuilt from `git archive 6ac69870` +
`patch -p1` of `pass-1.diff` in the session scratchpad (blobs 7215c887aa26 / 536d175cd605 /
16753577c693 = pass-1 fingerprints); ASTs with module / class / function docstrings stripped:
all three `AST-identical` to the current files. Positive control: HEAD `strings.py` vs current
reports `DIFFERS`. Pass 2 moved no code, so Performance and Mechanics owe nothing.

Attack: `rg -i "snake.?case"` over the package: every hit outside `strings.py` is the walker's
three reversal sites and their comments, plus `utils/__init__.py`'s two-helper line (the `utils/`
folder item's, as before). No doc under `docs/`, `tests/` or `examples/` pairs `field_map` with
snake case.

Not a finding, with trigger: "as declared" in the `FieldMeta.name` entry reads loosely for a
reverse relation with no `related_name` / `related_query_name`, whose `name` Django derives
(`ForeignObjectRel.name` -> `related_query_name()` -> `opts.model_name`). The load-bearing claims
(untransformed `field.name`, any case, the map key) are true for it too. Reopens if a caller or
doc reads the entry as "only names written in model source".

Disputes: none. New findings: none.

Verdict: verified.

Fingerprints (12 chars): `utils/strings.py` 991f7dad20b3; `optimizer/field_meta.py`
18ea719a6141; `tests/optimizer/test_multi_db.py` 88298e98d462; `optimizer/extension.py`
e0e53a8e10fc; `optimizer/walker.py` 73d6929a5881; `types/base.py` 49057fad2058.

Handoff: Read beyond the record: `optimizer/extension.py::DjangoOptimizerExtension._get_or_build_plan`
(plan cache + `exec_memo`), the walker's three `snake_case` callers, Django's
`ForeignObjectRel.name`. Open threads carried, none this item's to fix: F8 deferred
(`tests/utils/test_strings.py` provenance) for `## Outcomes`; `utils/__init__.py` two-helper
framing for the `utils/` folder Comments pass; `tests/optimizer/test_walker.py` provenance for the
walker item. The pytest `-p no:xdist` flag breaks the repo's `addopts` (`-n`/`--dist`
unrecognized); run Proof pytest lines exactly as written.
