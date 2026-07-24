# Fifth adversarial implementation review: row-preserving predicates Part 1

## Verdict

The latest revision closes the previous review's two concrete blockers in
their intended, tested forms:

- replacing one class-level `FILTER_DEFAULTS` entry now preserves an
  `extra`-only consumer policy and its original relation-filter wire shape;
- the live semantic signature reads the effective built form field's
  `to_field_name`, so the previously demonstrated post-validation mutation
  fails closed;
- the origin oracle now performs the same single MRO walk over the merged
  defaults/overrides mapping as django-filter;
- a framework-owned Relay relation `isnull` remains an upstream Boolean
  filter; and
- the exact Python 3.10 / Django 5.2.0 floor is now an ordinary push/PR CI
  node rather than a prose-only acceptance requirement.

Those are substantive corrections. Part 1 is nevertheless not ready for
sign-off. Two new blockers are independently reproducible:

1. framework-owned Relay relations still convert unsupported lookups such as
   `icontains` into GlobalID filters, contradicting Rev 11's own lookup policy
   and producing an execution-time `FieldError`; and
2. whole-entry identity is not an ownership boundary while the compared
   entries remain mutable and shared. A normal shallow copy followed by an
   in-place nested edit is still classified as the untouched base entry, so
   the consumer's policy is discarded during Relay conversion.

A newly added empty-GlobalID guard also turns a syntactically restrictive,
non-empty list into an unfiltered query. In addition, the implementation still
describes a finite “supported family” integrity model without making the
supported families executable, and the new signature matrix does not prove
the behavioral meaning of several values it claims to cover.

Only this review document was changed. The reproductions ran in isolated
processes with an in-memory fakeshop database setting; each process restored
the django-filter global it temporarily changed before exit. No tracked
database was opened or modified. Per repository policy, pytest was not run
because the request did not explicitly ask for a test run.

## Blocker 1 — unsupported Relay relation lookups still become GlobalID filters

The normative Relay wire-shape policy in the [Part 1 plan][part1-plan] now
states:

> Only the equality (`exact`) and membership (`in`) wire shapes convert.

`django_strawberry_framework/filters/sets.py::FilterSet.filter_for_lookup`
implements only three branches:

```python
if lookup_type == "isnull":
    return default_class, params
if lookup_type == "in":
    return GlobalIDMultipleChoiceFilter, ...
return cls._relay_filter_class_for_field(field), ...
```

The final unconditional return converts **every** other lookup, not only
`exact`. Pattern, range, ordering, and other lookups therefore acquire a
GlobalID wire shape even though neither Relay ID semantics nor the generated
filter can execute them.

### Reproduction

Registering `Genre` as a Relay target and declaring an explicit unsupported
lookup is sufficient:

```python
class BookFilter(FilterSet):
    class Meta:
        model = Book
        fields = {"genres": ["icontains"]}
```

The current checkout produces:

```text
GlobalIDMultipleChoiceFilter icontains _GlobalIDMultipleChoiceField
FieldError Unsupported lookup 'icontains' for ForeignKey or join on the field not permitted.
```

This is worse than a schema-build rejection: the invalid surface is generated
successfully, accepts a list-shaped GlobalID input, and fails only when the
query executes. It is also a direct implementation/specification
contradiction, not an omitted optional hardening.

The same fall-through applies to forward FK, reverse relation, and expanded
relation leaves. `FilterSet.get_fields` narrows an `"__all__"` declaration
after owner binding, but an explicit `Meta.fields` lookup still reaches this
path. The own-Relay-PK branch already handles the analogous case correctly by
raising a typed `ConfigurationError`.

### Required root-cause correction

Give framework-owned Relay relation lookups one shared exhaustive
classification, consumed by both generation stages:

```text
exact  -> GlobalIDFilter or GlobalIDMultipleChoiceFilter by relation cardinality
in     -> GlobalIDMultipleChoiceFilter
isnull -> upstream BooleanFilter
other  -> typed ConfigurationError at generation/finalization
```

Ownership must be decided first. If a consumer override actually governs the
selection, return that consumer filter unchanged; its class may intentionally
implement a nonstandard lookup. Apply the exhaustive lookup policy only to the
proven framework default. Do not merely pass unsupported framework defaults
through: the resulting upstream model-choice filter is not a valid
Relay-GlobalID contract either.

Required regressions:

- explicit unsupported lookup on a framework-owned forward FK, M2M, and
  reverse relation;
- the same shape through `RelatedFilter` expansion;
- a typed build/finalization error naming the filterset, field, and lookup,
  never a resolver-time Django `FieldError`;
- positive `exact`, `in`, and `isnull` controls with their scalar/list/Boolean
  annotations; and
- a consumer-owned relation override proving the package does not reject a
  lookup implemented by the consumer's own filter class.

## Blocker 2 — mutable shared entries defeat the whole-entry ownership check

`django_strawberry_framework/filters/sets.py::FilterSet._generation_origin_for_field`
now compares the selected entry to the corresponding
`BaseFilterSet.FILTER_DEFAULTS` entry with:

```python
if selected_entry is not base_entry:
    return "override_generated"
```

This fixes a shadow that **replaces** the nested entry. It does not establish
an immutable baseline. Both the outer mapping and every nested entry are
ordinary mutable dictionaries. A shallow copy intentionally reuses the nested
entry objects; mutating one of those objects changes the object on both sides
of the identity comparison.

That is not hypothetical metaprogramming. It is the natural alternative
spelling of an `extra`-only customization:

```python
shadow = dict(BaseFilterSet.FILTER_DEFAULTS)
shadow[models.ManyToManyField]["extra"] = lambda field: {
    "queryset": Genre.objects.none(),
    "required": True,
}


class BookFilter(FilterSet):
    FILTER_DEFAULTS = shadow

    class Meta:
        model = Book
        fields = {"genres": ["exact"]}
```

### Reproduction

The current checkout reports:

```text
capable False
selected_is_base True
origin FilterGenerationProvenance(
    origin='package_replacement',
    framework_added_distinct=True,
    expanded_from=(),
    generation_capable=False,
)
class GlobalIDMultipleChoiceFilter True
extra {'required': True}
token None
```

The capability gate correctly withholds the token because the outer
`FILTER_DEFAULTS` mapping is shadowed, but the earlier ownership decision has
already failed:

- the selected entry and “base” entry are the same mutated object;
- the origin oracle calls it `framework_default`;
- Relay conversion discards the consumer's `ModelMultipleChoiceFilter`;
- `_strip_model_choice_extras` removes the restricted queryset; and
- the replacement is stamped `package_replacement`.

Withholding the token only prevents correlated routing. It cannot restore the
consumer's lost validation policy or wire shape.

There is a second form of the same defect: mutating the inherited
`BaseFilterSet.FILTER_DEFAULTS` outer mapping in place leaves
`FilterSet._is_generation_capable()` true, classifies the mutated entry as the
base entry, converts it, and mints a token. The isolated reproduction produced:

```text
capable True
origin package_replacement
class GlobalIDMultipleChoiceFilter
token 2
```

The plan repeatedly calls the comparison target the “pure” or “unmodified”
base defaults. It is neither while it is a live mutable object also exposed as
the consumer extension hook.

### Required root-cause correction

Separate the package's canonical generation policy from django-filter's
mutable public extension mapping. The strongest design is:

1. create a package-owned copy of the supported upstream default policy;
2. freeze both the outer mapping and each nested entry, or store an immutable
   normalized record containing the selected class and `extra` provider;
3. make `FilterSet` use that package-owned baseline;
4. require consumers to replace an entry in a shadowed mapping rather than
   mutate shared package state; and
5. have generation and ownership consume the same immutable selection result.

A shallow consumer copy can then safely reuse unchanged immutable entries,
while an attempted nested mutation fails loudly and a deliberate replacement
is unambiguously consumer-owned. Comparing against a deep snapshot without
preventing later shared mutation is weaker: it may detect drift, but it still
allows one consumer to contaminate every other filterset process-wide.

Required regressions:

- shallow outer copy plus nested `extra` mutation;
- direct in-place mutation through an inherited defaults mapping;
- proof that one filterset's customization cannot alter an unrelated
  filterset;
- observable restricted queryset and wire-shape preservation, not merely a
  token assertion; and
- positive controls for unchanged canonical entries and an explicit
  replacement entry.

Do not address this only in `_is_generation_capable`. Relay conversion happens
before the capability token can protect anything.

## High 3 — an empty-node-id list silently widens a restrictive filter

`django_strawberry_framework/filters/base.py::GlobalIDMultipleChoiceFilter.filter`
now drops decoded node IDs in django-filter's `EMPTY_VALUES` and returns the
incoming queryset when nothing remains:

```python
node_ids = [node_id for node_id in node_ids if node_id not in EMPTY_VALUES]
if not node_ids:
    return qs
```

This avoids the previous integer-binding `ValueError`, but the chosen behavior
is unsafe and contradicts the filter's own restrictive-empty contract:

```text
id: {in: []}                         -> match no rows
id: {in: ["<well-formed type:>"]}    -> match every row
```

A client can therefore turn a non-empty restrictive membership condition into
no condition merely by supplying a well-formed GlobalID with an empty node-id
component. A mixed list silently ignores that element while accepting the
rest, unlike malformed or wrong-type GlobalIDs, which reject the whole input
and name the offending index.

The existing single-value no-op in
`django_strawberry_framework/filters/base.py::GlobalIDFilter.filter` is not a
sound precedent. It is the same silent-widening issue on a scalar input, and
duplicating it into the list path makes the behavior harder to correct later.
“Decodable as `type_name:`” does not make an empty identifier a valid resource
identifier.

The root fix should live in the shared
`django_strawberry_framework/filters/base.py::_decode_and_validate_global_id`
boundary: reject an empty decoded `node_id` with the existing
`GLOBALID_INVALID` error code, including the list index when present. Apply
that rule consistently to the single and multiple filters. If the project
deliberately prefers a non-error policy, match-none is the only
non-widening alternative; returning the unfiltered queryset is not.

Add live regressions for scalar, all-empty list, and mixed empty/real list
inputs. Each should prove the response/error contract and that the root query
does not silently return unrelated rows.

## High 4 — “supported generated families” is prose, not an executable fail-closed boundary

The plan and
`django_strawberry_framework/filters/sets.py::_CandidateFingerprint` describe a
finite integrity boundary for “the supported generated django-filter
families.” No production object enumerates those families or selects a
family-specific behavior profile.

`django_strawberry_framework/filters/sets.py::_candidate_metadata_for` marks
any framework-origin leaf on a many-side path eligible based only on path and
`method is None`. If the class is generation-capable, the generic
`_fingerprint_of` tuple is applied to whatever filter class upstream selected.
An unknown family introduced by an unbounded future `django-filter>=25.2`
release therefore becomes routable before its runtime reads have been audited.
The mutable-default reproduction above demonstrates the same architectural
gap today: changing the base mapping can place different behavior behind a
supposed framework origin.

The previous exact-class allowlist was correctly withdrawn because upstream
creates dynamic `ConcreteInFilter` and `ConcreteRangeFilter` subclasses. That
does not require a class-agnostic authorization boundary. Use an executable
behavior-profile registry:

- identify supported base families by a controlled MRO/profile match;
- normalize the effective runtime values each family actually reads;
- let dynamic `in`/`range` subclasses inherit the relevant base profile;
- return no profile for an unknown or ambiguous family; and
- make “no profile” ineligible, so upstream additions fail closed to the outer
  invocation until audited.

This consolidates the repeated signature inventory in the plan, glossary,
dataclass, fingerprint builder, and applicator into one executable source of
truth. It also makes the claim “a family whose state cannot be normalized is
ineligible” true by construction rather than by review discipline.

## High 5 — the signature matrix proves inequality, not the semantics of several fields

The [Part 1 plan][part1-plan] says every enumerated signature member has a
fail-closed row in the **parameterized** matrix. The parameterized instance
matrix in `tests/filters/test_sets.py` covers only:

- `get_method`;
- `is_noop`;
- `get_filter_predicate`;
- effective `field.to_field_name`;
- `conjoined`;
- `always_filter`; and
- `null_value`.

Other fields are scattered across older tests (`.filter`, pk qualification,
and `distinct`) or have no equivalent capable-live-mutation acceptance row
(`field_name`, `lookup_expr`, `method`, `exclude`, and wholesale class
replacement). The prose claim is therefore inaccurate even if the tuple
implementation itself is straightforward.

More importantly, several new rows mutate a value without making that value
behaviorally relevant:

- `conjoined=True` is tested with only one submitted genre, so AND and OR are
  identical;
- `always_filter=False` is tested while `required=False`, so `is_noop` remains
  false;
- `null_value` is changed to a sentinel that is never submitted; and
- helper replacements delegate to the original behavior unchanged.

Those cases prove only that dataclass equality notices a changed attribute.
They cannot catch a signature field that reads the wrong construction proxy,
which was exactly how the prior `to_field_name` blocker survived despite the
field being present in the tuple.

Build the matrix from the executable family profiles recommended above. Each
row should supply:

1. a frozen/runtime normalization mutation;
2. input and fixtures that make the mutated value alter the original filter's
   predicate or no-op decision;
3. a pre-fanned outer queryset that distinguishes correlated routing from the
   required outer fallback; and
4. the common token-equality, signature-divergence, alias-absence, SQL-shape,
   ordered-row, and count assertions.

For example, `conjoined` needs two selected relations and rows that distinguish
OR from AND. `null_value` needs the submitted sentinel and a nullable relation.
`get_method` should switch filter to exclude rather than call an
effect-identical delegate. Keep separate class-descriptor rows for every
callable profile member.

## Medium 6 — the new reachable GlobalID behavior is tested at the wrong tier

The empty-node-id branches added to
`GlobalIDMultipleChoiceFilter.filter` are covered only by predicate-capturing
stubs in `tests/filters/test_base.py`. The same code is directly reachable
through the existing fakeshop `/graphql/` surface:
`allLibraryGenres(filter: {id: {in: [...]}})` already exercises
`GlobalIDMultipleChoiceFilter` and has live wrong-type, malformed, ordinary
list, and explicit-empty-list coverage.

The repository's live-first rule and the [test-query tier guide][test-query-readme]
therefore require the new consumer-visible behavior to be earned in
`examples/fakeshop/test_query/`, not solely through a package stub. A small
package test may remain for the exact low-level predicate shape, but it cannot
be the acceptance test.

The Relay-relation `isnull` correction also needs at least one schema-level
annotation/coercion assertion. The current tests prove the Python filter class
and direct queryset rows, but not that the generated GraphQL input is Boolean
and accepts `true`/`false` without the former GlobalID/list coercion. Use a live
fakeshop surface if one already exposes a direct Relay relation `isnull`;
otherwise an in-process package schema test is the justified fallback.

The existing row-preserving live coverage and its descriptions in the
[test-query tier guide][test-query-readme] remain aligned: both direct-deep and
expanded origins, SQL shape, mixed OR, `totalCount`, cursor, and page-boundary
claims are represented. The gap is limited to the newly introduced Rev 11
GlobalID/Boolean behavior.

## Medium 7 — Rev 11 folds unrelated input-validation fixes into the Part 1 contract

The row-preserving predicate plan now owns:

- correlated-`EXISTS` classification and application;
- Relay conversion ownership;
- relation `isnull` wire correction; and
- empty decoded GlobalID semantics.

The first two are integral to safe adapter authorization. Relation `isnull` was
exposed by the same conversion branch and reasonably belongs in the repair.
Empty-node-id validation is different: it is a general GlobalID input contract
shared by scalar and list filters and does not depend on row preservation.

Keeping that change in Rev 11 without adding it to the standing GlobalID
contract makes Part 1 the only source of truth for a broadly visible input
rule. Move the normative empty-ID decision into the appropriate GlobalID/filter
specification or glossary section and let Part 1 reference it as a discovered
dependency. This is especially important if the correct fix changes the
existing scalar no-op to `GLOBALID_INVALID`.

## What is satisfactorily closed

The following prior findings are closed and should remain closed:

- a replaced `FILTER_DEFAULTS` entry is consumer-owned by its whole entry,
  including an `extra`-only replacement;
- merged-map/MRO precedence now agrees with
  `BaseFilterSet.filter_for_lookup`, including an override shadowed by a
  more-derived default;
- live `field.to_field_name` mutation is observed from the built form field;
- build-time form-field inspection happens on a disposable deepcopy;
- the previously missing helper descriptors and execution knobs are present
  in the signature tuple;
- a relation `isnull` is no longer converted to a GlobalID filter;
- the shared pk-qualified-path helper removes the duplicated single/multiple
  derivation;
- the Python 3.10 / Django 5.2.0 floor is pinned in CI;
- the PostgreSQL artifact/footer checks, Medtrics fixture, direct and expanded
  live proofs, test-scoped Loan connection, and multi-database coverage remain
  architecturally sound; and
- the tracked SQLite delta now has an explicit single-row provenance contract
  in the plan rather than remaining unexplained binary churn.

The core classifier, neutral correlated predicate primitive, and multiset
selection contract remain the right architecture. The remaining blockers are
at the authorization and GraphQL wire boundaries around that core.

## Recommended correction order

1. Make framework-owned Relay relation lookup handling exhaustive and reject
   every lookup outside `exact` / `in` / `isnull` at build time.
2. Replace mutable `BaseFilterSet.FILTER_DEFAULTS` identity with a
   package-owned immutable generation-policy baseline.
3. Reject empty decoded node IDs consistently in the shared GlobalID decoder;
   never widen a restrictive filter.
4. Replace the class-agnostic generic signature with executable
   per-supported-family behavior profiles that fail unknown families closed.
5. Derive a genuinely behavioral acceptance matrix from those profiles and
   move reachable GlobalID cases to live HTTP.
6. Reconcile the plan, glossary, and GlobalID documentation after the behavior
   is fixed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[part1-plan]: row-preserving-predicates-part1-plan.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
