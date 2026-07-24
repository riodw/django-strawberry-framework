# Fourth adversarial implementation review: row-preserving predicates Part 1

## Verdict

The latest revision closes the previous review's concrete probes:

- generated-filter helper overrides are now part of the signature;
- a consumer `FilterSet.__init__` override prevents capability-token minting;
- Relay relation overrides that replace the filter class survive direct and
  expanded generation;
- the expanded non-pk-`to_field` `in` path now has a complete adapter regression;
- the PostgreSQL artifact generator emits its canonical footer and has a
  regeneration guard; and
- the stale provenance documentation was replaced with the finite-boundary
  contract.

Those corrections are substantive. Part 1 is still not ready for sign-off,
however. Two independently reproducible ownership/integrity failures remain:

1. a shadowed class-level `FILTER_DEFAULTS` entry is recognized as
   consumer-owned only when its `filter_class` changes, so an `extra`-only
   override is still discarded by Relay conversion; and
2. the signature records the constructor copy of `to_field_name`, while
   django-filter executes against the mutable live form-field value.

The first silently removes a documented django-filter customization. The
second reopens the pre-fanned multiplicity failure that the signature was
introduced to prevent. Both contradict the normative authorization state
machine in the [Part 1 plan][part1-plan] and the shipped claim in the
[glossary][glossary].

No production files were changed during this review. The reproductions ran in
isolated in-memory fakeshop databases and did not touch the tracked SQLite
file. Per repository policy, pytest was not run because the request was for a
code review, not an explicit test run.

## Blocker 1 — `FILTER_DEFAULTS` ownership still compares only the filter class

The new Relay ownership boundary in
`django_strawberry_framework/filters/sets.py::FilterSet._generation_origin_for_field`
does not identify the complete django-filter selection. For a shadowed
class-level `FILTER_DEFAULTS`, it compares only:

```python
shadowed.get("filter_class") is not base.get("filter_class")
```

That is insufficient. A `FILTER_DEFAULTS` entry is a generation policy
containing both `filter_class` and `extra`. Changing only `extra` is a normal
django-filter customization: it can restrict the relation queryset, select a
`to_field_name`, change requiredness, or supply other constructor state while
deliberately retaining the standard filter class.

Upstream
`django_filters.filterset.BaseFilterSet.filter_for_lookup` consumes both parts.
The package origin oracle consumes only one. The two paths therefore disagree
about ownership.

### Reproduction

The reproduction registered `Genre` as a Relay-node target and shadowed the
M2M default with the **same** upstream
`ModelMultipleChoiceFilter` class but a consumer-owned `extra` factory:

```python
base = dict(
    django_filters.filterset.BaseFilterSet.FILTER_DEFAULTS[
        models.ManyToManyField
    ],
)


class BookFilter(FilterSet):
    FILTER_DEFAULTS = {
        **django_filters.filterset.BaseFilterSet.FILTER_DEFAULTS,
        models.ManyToManyField: {
            "filter_class": base["filter_class"],
            "extra": lambda field: {
                "queryset": Genre.objects.none(),
                "required": True,
            },
        },
    }

    class Meta:
        model = Book
        fields = {"genres": ["exact"]}
```

The current checkout produced:

```text
class GlobalIDMultipleChoiceFilter
is_global True
origin FilterGenerationProvenance(
    origin='package_replacement',
    framework_added_distinct=True,
    expanded_from=(),
    generation_capable=False,
)
extra {'required': True}
candidate CandidateFilterMetadata(... eligible=True, fingerprint=None, token=None)
```

The consumer's filter class happens to equal the base class, but its generation
policy does not. The package nevertheless:

- classifies the selection as `framework_default`;
- replaces it with `GlobalIDMultipleChoiceFilter`;
- strips the consumer's relation queryset as a model-choice-only extra;
- stamps the result `package_replacement`; and
- publishes a framework candidate row.

The absent token prevents correlated routing, but it cannot recover the filter
class, queryset validation, or wire shape already discarded during generation.
This is the same public-surface loss as the prior Relay override blocker through
an untested half of the same extension API.

It also directly falsifies the glossary statement that a shadowed
`FILTER_DEFAULTS` “keeps its own wire shape and is never converted to a package
GlobalID primitive.”

### Required root-cause correction

Model the result of django-filter's lookup-default selection as one explicit,
immutable ownership-bearing value rather than independently inferring ownership
from one member of its mapping.

The selection must include at least:

- the resolved selection field and lookup;
- the effective default entry selected through the field-class MRO;
- the selected `filter_class`;
- the selected `extra` provider and its effective constructor parameters; and
- whether that entry came from the unmodified base defaults,
  `Meta.filter_overrides`, or a class-level `FILTER_DEFAULTS` shadow.

`filter_for_lookup` and `filter_for_field` must consume that single verdict.
Any consumer change to the effective selected entry — class, `extra`, or other
generation policy — remains consumer-owned, is returned unchanged, and is
ineligible. A package GlobalID replacement is legal only when the **entire**
effective selection is proven to come from the unmodified framework default.

For the current dictionary shape, identity of the selected entry is a safer
minimum than comparing only `filter_class`: an ordinary shallow
`{**BaseFilterSet.FILTER_DEFAULTS}` copy retains the original nested entry
objects for untouched field classes, while replacing one entry gives the
changed class an independent object. A fully normalized selection result is
still the stronger architecture because it prevents the ownership oracle and
upstream parameter construction from drifting again.

Required regressions:

- direct M2M and forward-FK Relay relations with the same base filter class but
  a different `extra` factory;
- an observable restricted queryset or non-default `to_field_name`, not only a
  class assertion;
- expansion through `RelatedFilter`;
- unchanged consumer wire shape, `origin="override_generated"`, no candidate
  row, and no reserved predicate alias; and
- a positive control showing an untouched entry in a shallow copied defaults
  mapping is not falsely treated as modified unless the specification
  deliberately makes any `FILTER_DEFAULTS` shadow globally consumer-owned.

Do not fix this by withholding only the token or relabeling the replacement.
The consumer object must survive generation.

## Blocker 2 — the signature signs declared constructor state, not the effective runtime field

`django_strawberry_framework/filters/sets.py::_fingerprint_of` records:

```python
(filter_instance.extra or {}).get("to_field_name")
```

The accompanying source and plan describe that as the effective relation
target. It is not. django-filter's
`MultipleChoiceFilter.get_filter_predicate` executes against:

```python
self.field.to_field_name
```

`filter.field` is a lazily built, cached form field on the live per-request
filter. Once built, its `to_field_name` can diverge from `extra` without
changing any signed value. The implementation deliberately avoids reading the
built field because the field object itself is not equality-stable across
deepcopy, but the string/`None` attribute that runtime actually consumes **is**
normalizable. Signing the declaration instead of the effective read leaves the
authorization boundary incomplete.

### Reproduction

The reproduction used the same eligible generated `Book.genres`
`ModelMultipleChoiceFilter` family as the prior helper-mutation finding and a
Book queryset pre-fanned by two Loan rows.

Two genres were created:

- the submitted genre had pk `1` and name `"2"`;
- the book was related to genre pk `2`.

After validation built the live filter field, the reproduction changed only:

```python
leaf.field.to_field_name = "name"
```

The constructor state remained `extra["to_field_name"] is None`. The submitted
genre instance therefore contributed its name `"2"` to
`get_filter_predicate`, redirecting the effective predicate to genre pk `2`.

The current checkout produced:

```text
before effective None extra None
token_equal True
fingerprint_equal True
effective_to_field name
routed [1, 1]
outer [1]
```

The token and signature still authorize the correlated adapter. It suppresses
the framework `distinct` and preserves the two incoming Book occurrences. The
original outer invocation — the required fail-closed behavior for a
consumer-mutated live filter — honors `distinct` and returns one occurrence.

This is a result-set regression at the exact multiset boundary Part 1 promises
to protect. It is not merely an over-broad documentation claim.

### Required root-cause correction

The semantic integrity model must normalize the values the effective
implementation reads at execution, not proxies from which those values were
originally constructed.

For `ModelMultipleChoiceFilter`, the normalized runtime signature must include
the effective `filter_instance.field.to_field_name`. A sound build-time capture
can force form-field construction on a disposable deepcopy of the generated
filter and record only the primitive string/`None` value; the request-time
capture can read the same primitive from the live field. This avoids comparing
queryset or form-field object identity while still signing the actual runtime
input.

The same audit must cover the rest of the helper call graph by following real
runtime reads:

- `is_noop` reads `extra["required"]` and the effective field choices when
  `always_filter` is false;
- `get_filter_predicate` reads the effective form-field target;
- the package GlobalID filters read their live parent/owner definition during
  decode and validation; and
- future django-filter upgrades may add state to these supported families.

The root abstraction should therefore be a per-supported-family normalized
behavior schema, with tests derived from that schema, rather than an
ever-growing generic tuple whose completeness is asserted manually. If a
family's effective state cannot be normalized safely, that family must be
ineligible until it can be proven safe.

Add an end-to-end pre-fanned regression for the live
`field.to_field_name` mutation above. It must assert token equality, signature
mismatch, the original outer result, and absence of the reserved alias.

## High 3 — the normative signature matrix is still under-tested

The Part 1 plan explicitly enumerates `.filter`, `get_method`,
`get_filter_predicate`, `is_noop`, the pk-qualification marker,
`to_field_name`, `conjoined`, `always_filter`, and `null_value` as the finite
authorization boundary.

The committed end-to-end signature tests currently exercise:

- `.filter`;
- `get_filter_predicate`;
- the pk-qualification marker; and
- `distinct`.

There is no focused fail-closed regression for:

- `get_method`;
- `is_noop`;
- effective `field.to_field_name`;
- `conjoined`;
- `always_filter`; or
- `null_value`.

Blocker 2 demonstrates why implementation-by-enumeration requires an
acceptance row for every enumerated member: a field named in the plan and
dataclass can still represent the wrong runtime value. Parameterize a shared
pre-fanned fail-closed harness across every signature member and assert the
same four invariants for each: the token remains equal, the signature diverges,
the reserved alias is absent, and the original outer invocation's result wins.

Tests for helper descriptors should cover both instance overrides and
class-level descriptor replacement, because the signature intentionally has
separate halves for those cases. Tests for the execution knobs should use
values that make the mutation observably change behavior rather than checking
dataclass inequality alone.

## Medium 4 — the specification and standing documentation overstate the current implementation

The [Part 1 plan][part1-plan], [glossary][glossary], and implementation
docstrings now agree on a finite rather than universal mutation boundary. That
is an improvement. Two statements within that finite contract are still false:

- a shadowed `FILTER_DEFAULTS` does not necessarily keep its wire shape
  (Blocker 1); and
- the signature does not record the effective `to_field_name` runtime reads
  (Blocker 2).

Correct the implementation first, then keep one canonical inventory of the
supported-family behavior schema and have the plan/glossary summarize it. The
current repeated inventories in `_CandidateFingerprint`, `_fingerprint_of`,
`FilterSet._apply_flat_leaves`, the plan, and the glossary are already
expensive to reconcile and made it easy for “constructor state” to be described
as “effective state.”

The plan header also remains “Rev 8,” while its body now contains several
“round-4” normative amendments introduced after the Rev 8 history paragraph.
Either advance the revision/history or remove revision-number narration in
favor of source-control history; the current identity makes it unclear which
contract was actually reviewed.

## Medium 5 — the tracked SQLite delta is still unrelated to the stated change

Commit `94054416` changes `examples/fakeshop/db.sqlite3` from blob
`feace7e4…` to `c0e1280…`, at the same byte size. The PostgreSQL capture script
explicitly states that it never opens the tracked SQLite file, its seed is
rolled back on PostgreSQL, and no migration or canonical seed change in the
commit requires a new SQLite image.

If the database update records an intentional Kanban/glossary source-of-truth
change, document the logical rows changed and regenerate it through that
owner's workflow. Otherwise it remains unrelated binary churn and should be
removed from the change. A clean git status does not make an opaque committed
database delta self-explanatory.

## What is now satisfactorily closed

The following prior findings are closed and should remain closed while the two
new blockers are repaired:

- own class-body declarations borrowed from generated leaves are
  unconditionally restamped `declared` and stripped of generation tokens;
- instance helper mutation is no longer authorized merely because `.filter`
  itself is unchanged;
- a consumer `__init__` override makes the generating class non-capable;
- Relay relation overrides that change the selected filter class survive
  direct FK, direct M2M, expanded, and observable outer-execution paths;
- the forward Relay FK `in` lookup remains list-shaped;
- the expanded `children__target__in` non-pk-`to_field` path composes lookup
  selection, marker rebasing, token verification, correlated execution, SQL
  shape, and restrictive empty-list semantics;
- the PostgreSQL artifact generator now emits the canonical ten-group footer,
  and a pure test guards the checked-in artifact tail;
- the PostgreSQL regression drives the real `LoanFilter` path;
- the stale “harmless residual” provenance statement is gone; and
- `docs/TREE.md` includes the new package-test files. Its documented trees do
  not catalog arbitrary `docs/` and `scripts/` files, so the absence of the
  artifact/capture script from that scoped tree is not itself a remaining
  defect.

The classifier, correlated-`EXISTS` primitive, live HTTP coverage, Medtrics
fixture, connection pagination proof, and PostgreSQL evidence remain
architecturally sound. The remaining problem is narrower: ownership and
semantic authorization still model only part of the effective django-filter
selection/execution state.

## Recommended correction order

1. Preserve an `extra`-only class-level `FILTER_DEFAULTS` selection before
   Relay conversion.
2. Replace constructor-only `to_field_name` signing with normalization of the
   effective runtime field value and audit every runtime read in each eligible
   family.
3. Turn the finite signature inventory into a parameterized acceptance matrix.
4. Reconcile the plan, glossary, and source inventories with that executable
   schema and advance the plan revision identity.
5. Remove or explain the tracked SQLite binary delta.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: GLOSSARY.md#filterset
[part1-plan]: row-preserving-predicates-part1-plan.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
