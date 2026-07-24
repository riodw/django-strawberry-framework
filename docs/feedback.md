# Third adversarial implementation review: row-preserving predicates Part 1

## Verdict

The latest revision closes the three concrete defects from the second review:

- an own class-body declaration now transitions unconditionally to
  `origin="declared"` and loses any borrowed generation token;
- the live signature now includes the non-pk-`to_field` marker and the
  directly assigned / class-level `.filter` implementation;
- a forward Relay relationship using `in` now preserves the lookup-aware
  `GlobalIDMultipleChoiceFilter`; and
- the PostgreSQL artifact, `exclude=True` invariant, glossary text, live-test
  guide, and previously omitted relation-fixture tree entries have been added.

Those are real improvements and their focused regressions exercise the intended
production paths. Part 1 is still not ready for final sign-off, however. The
authorization model remains incomplete in two independently reproducible ways:

1. the “canonical semantic signature” does not cover the effective behavior
   dynamically invoked by django-filter filters; and
2. `Meta.filter_overrides` on a Relay relation is discarded and reclassified as
   a safe package replacement.

Both violate the normative fail-closed contract in the [Part 1 plan][part1-plan].
The first can change the multiplicity of a consumer-mutated, pre-fanned input.
The second silently replaces a consumer-owned filter before the live gate is
even reached.

No production files were changed during this review. Per repository policy,
pytest was not run because this was a review request rather than an explicit
test-run request. The results below were reproduced in isolated Django
processes against the current checkout; the multiplicity reproduction used an
in-memory migrated fakeshop database and did not touch the tracked SQLite file.

## Blocker 1 — the semantic signature still does not identify the effective filter behavior

The expanded
`django_strawberry_framework/filters/sets.py::_CandidateFingerprint` records:

- the concrete class;
- `field_name`, `lookup_expr`, `method`, `exclude`, and `distinct`;
- an instance-level `.filter` assignment and the class-level `.filter`
  descriptor;
- the non-pk-`to_field` marker; and
- `conjoined`, `always_filter`, and `null_value`.

That is stronger than the prior tuple, but it is not the “single-source
semantic signature” claimed by the source and plan. Capturing the top-level
`.filter` descriptor does not capture the helpers that descriptor dispatches
through dynamically.

For example, django-filter's generated `ModelMultipleChoiceFilter` inherits a
`.filter()` implementation that calls all of the following on the live
instance:

```text
self.is_noop(...)
self.get_method(...)
self.get_filter_predicate(...)
self.field.to_field_name
```

None of those effective callables, instance overrides, or the effective
relation target stored on the form field is represented by
`_CandidateFingerprint`. A consumer can therefore mutate a generated live
filter through a normal django-filter extension seam while retaining both the
token and an equal signature.

### Reproduction

The reproduction used a generated `Book.genres` `ModelMultipleChoiceFilter`,
which is an eligible direct M2M candidate. Its incoming queryset was
deliberately pre-fanned by two `Loan` rows for the same `Book`. After form
validation, the live filter's `get_filter_predicate` was assigned a
consumer-owned callable with the same predicate result:

```python
leaf.get_filter_predicate = lambda value: {"genres": value}
```

The current checkout produced:

```text
authorized True True
routed [1, 1]
outer [1]
```

The two authorization booleans mean the live token still equals the frozen
token and `_fingerprint_of(leaf) == candidate.fingerprint`. The routed adapter
therefore suppresses the filter's `distinct` and preserves the two incoming
rows. The original outer invocation—the behavior the fail-closed contract
promises for a consumer-mutated filter—honors `distinct` and returns one row.

This is a consumer-visible compatibility regression, not merely an internal
metadata imperfection. It is the exact pre-fanned multiplicity boundary that
the Part 1 multiset contract deliberately leaves under consumer ownership.

Other variants exist without changing `.filter` itself:

- replace `get_method` to change `filter` versus `exclude`;
- replace `is_noop` to change whether a restrictive leaf is applied;
- replace `get_filter_predicate` to target a different lookup; or
- change `field.to_field_name` / the constructor state from which that field is
  built.

Adding only `get_filter_predicate` to the tuple would close one probe while
leaving the abstraction wrong.

### Required root-cause correction

The authorization boundary needs an explicit, complete integrity model for the
supported generated filter families:

1. Treat a consumer override of `FilterSet.__init__` as a generation-capability
   break. `__init__` is the standard place a consumer replaces or mutates
   `self.filters`; checking only `filter_for_field`, `filter_for_lookup`, and
   `FILTER_DEFAULTS` knowingly leaves that ordinary seam open.
2. Define one normalized runtime-behavior signature for the package-generated
   invocation. It must cover the effective helper call graph and state used by
   every eligible django-filter family, including instance and class overrides
   of `get_method`, `get_filter_predicate`, and `is_noop`, plus the effective
   relation target (`field.to_field_name`) and any execution-relevant
   constructor state.
3. Prove the normalization is deepcopy-stable on the exact dependency floor
   (Python 3.10, Django 5.2.0, and the supported django-filter floor) and on the
   current matrix. Querysets and form fields cannot be compared by object
   identity, so any structural normalization must state how those values are
   represented.
4. Add a pre-fanned multiplicity regression using an instance helper override,
   not only a `.filter` replacement. It must assert the original outer result,
   absence of a reserved alias, and token-equality/signature-mismatch.

If arbitrary post-construction mutation is intentionally outside the supported
contract, the plan, glossary, and source must stop claiming that **any**
consumer mutation fails closed. That would be a material narrowing of the
current specification, not a documentation-only cleanup. The higher-quality
resolution is to make the stated integrity boundary true.

## Blocker 2 — Relay conversion erases `Meta.filter_overrides` ownership

The plan says `Meta.filter_overrides` products are consumer-origin,
immediately ineligible, and preserve today's outer invocation byte-for-byte.
That is true for the scalar tests currently committed, but false for a relation
whose target implements Relay `Node`.

The sequence in [the FilterSet implementation][filter-sets] is:

1. upstream `BaseFilterSet.filter_for_lookup` selects the consumer's relation
   override;
2. `FilterSet.filter_for_lookup` sees a Relay target and replaces that selected
   class with `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`;
3. `FilterSet.filter_for_field` reconstructs `type(default)`, which is now the
   package GlobalID class rather than the consumer class; and
4. the replacement is stamped unconditionally as `origin="package_replacement"`.

The resolved-field origin oracle is therefore bypassed at the exact Relay
replacement boundary it is supposed to govern.

### Reproduction

The reproduction registered `Genre` as a Relay-node target and declared:

```python
class CustomRelationFilter(django_filters.ModelMultipleChoiceFilter):
    pass


class BookFilter(FilterSet):
    class Meta:
        model = Book
        fields = {"genres": ["exact"]}
        filter_overrides = {
            models.ManyToManyField: {
                "filter_class": CustomRelationFilter,
            },
        }
```

The current checkout produced:

```text
GlobalIDMultipleChoiceFilter
FilterGenerationProvenance(
    origin='package_replacement',
    framework_added_distinct=True,
    expanded_from=(),
    generation_capable=True,
)
candidate present: True
eligible/token: True True
```

The consumer's `CustomRelationFilter` is absent, the live surface is marked
package-owned, and the candidate is authorized. This is more severe than a
false-positive optimization: the consumer override has already been discarded,
so failing closed later cannot recover its behavior.

The same architectural question applies to a relation governed by a
class-level `FILTER_DEFAULTS` override. The current capability check prevents a
token from being minted, but Relay conversion can still replace the
consumer-selected filter class before the outer invocation.

### Required root-cause correction

Resolve filter ownership once, before any Relay transformation, and carry that
decision through `filter_for_lookup` and `filter_for_field`:

- a consumer-selected `Meta.filter_overrides` or `FILTER_DEFAULTS` product must
  be returned unchanged and remain consumer-origin/ineligible;
- a package GlobalID replacement may be constructed and stamped
  `package_replacement` only when the upstream selection is proven to be the
  framework default;
- `filter_for_lookup` and `filter_for_field` must consume one shared selection
  result rather than independently rediscovering lookup class, Relay shape, and
  origin; and
- the Relay wire-shape policy for an explicit consumer relation override must
  be documented. Under the plan's current byte-for-byte rule, the override owns
  that shape; the framework must not silently force it back to a package
  GlobalID primitive.

Required regressions should cover forward FK and M2M relation overrides, both
direct and through `RelatedFilter` expansion, plus a class-level
`FILTER_DEFAULTS` relation override. At least one test must make the custom
filter return observably different rows and prove no candidate row or reserved
predicate alias exists.

Do not repair this by merely stamping the package replacement
`override_generated`. That would prevent correlated routing but would still
discard the consumer's filter—the primary defect.

## High 3 — the non-pk-`to_field` list path is not yet proven through the adapter

The forward Relay `in` generation defect is fixed at its source, and the new
tests prove:

- generated FK-to-pk and FK-to-non-pk-`to_field` leaves are
  `GlobalIDMultipleChoiceFilter`;
- the input annotation is list-shaped;
- primitive execution decodes every GlobalID; and
- the non-pk target is compared through `relation__pk__in`.

The complete cross-product is still missing. The only parent-FilterSet
authorization/`EXISTS` regression for the non-pk-`to_field` fixture uses the
scalar `exact` leaf. The new `in` tests invoke the generated child leaf
directly on the child queryset; they do not expand it across the reverse
`children` prefix, mint and verify its candidate capability, or execute it
inside the correlated adapter.

Add one `ParentFilter` regression for the generated expanded
`children__target__in` leaf over targets whose pk differs from the stored
`to_field` value. It should prove:

- the expanded live class and list annotation;
- marker and token survival through deepcopy/rebasing;
- one correlated `EXISTS`, no outer join or `DISTINCT`;
- correct rows for two encoded target pks; and
- restrictive empty-list behavior through the adapter.

This is a remaining acceptance gap rather than a reproduced production
failure, but it is the only test that composes all three recently corrected
mechanisms: lookup-aware `in`, non-pk pk-qualification, and live
candidate authorization.

## High 4 — the PostgreSQL artifact is not reproducible under the repository documentation contract

The new [PostgreSQL artifact][pg-artifact] is valuable evidence. It contains the
actual emitted SQL, parameterized SQL, environment, deterministic seed size,
shape assertions, and `EXPLAIN (ANALYZE, BUFFERS)` output. The accompanying
[PostgreSQL regression][pg-test] also drives the real `LoanFilter` production
path.

However, [the capture script][pg-capture] does not emit the mandatory canonical
link-definition footer. The checked-in artifact currently contains all ten
required group headers, but `scripts/capture_pg_predicate_explain.py::main`
ends after the environment section and immediately calls
`ARTIFACT_PATH.write_text(...)`. Running the documented regeneration command
therefore removes:

```text
<!-- LINK DEFINITIONS -->
<!-- Root -->
...
<!-- External -->
```

That makes the generated file differ from its generator and leaves a
“do not hand-edit” artifact that cannot be regenerated without violating the
standing-document rule. The generator must render the canonical footer itself,
and a test should assert the generated document passes the same link-block
validation as other standing docs.

[The tree][tree] also omits all three newly introduced PostgreSQL-evidence
paths:

- `docs/row-preserving-predicates-part1-pg-explain.md`;
- `scripts/capture_pg_predicate_explain.py`; and
- `tests/test_predicate_pg_explain.py`.

The relation-fixture omissions from the prior review are fixed, but the new
files created while fixing the planner-evidence gap introduced a second round
of tree drift. Regenerate `docs/TREE.md` through its owner rather than adding
these entries by hand.

## Medium 5 — source and standing-document claims contradict the implementation

`django_strawberry_framework/filters/sets.py::FilterGenerationProvenance`
still contains the old statement that a consumer `filter_for_field` mutation
cannot be detected and that the residual is “harmless” because eligibility is
decided purely from path, provenance, and `method`. The new architecture was
introduced precisely because that statement is false: live token/signature
verification now exists to fail those mutations closed.

Elsewhere, `_CandidateFingerprint`, `_fingerprint_of`,
`FilterSet._apply_flat_leaves`, [the Part 1 plan][part1-plan], and
[the glossary][glossary] make the opposite over-broad claim: the signature
covers every behavior-changing state and any consumer mutation runs the
original outer invocation. Blocker 1 disproves that claim.

After the integrity model is corrected:

- remove the obsolete “harmless residual” text;
- describe the exact capability and signature boundary once;
- make the plan, glossary, and implementation docstrings use the same finite
  contract; and
- keep local comments focused on why a particular state element is normalized,
  rather than repeating a total-safety claim at several sites.

This is not cosmetic. Contradictory source contracts make later django-filter
upgrades difficult to audit and encourage new execution knobs to be added
without updating authorization.

## Medium 6 — tracked SQLite binary churn remains unexplained

`examples/fakeshop/db.sqlite3` is still modified at the same byte size, while
the current production/test changes do not add a migration or document a seed
fixture update requiring a new tracked database image.

Restore the binary if the change is test residue. If it is intentional,
regenerate it through the repository's owning seed workflow and document the
logical fixture change that requires it. An opaque SQLite delta should not ride
with a predicate-compiler implementation.

## What is now satisfactorily closed

The following prior findings should remain closed while the two authorization
blockers are repaired:

- own declarations borrowed from generated leaves are restamped `declared`,
  stripped of their token, absent from the final candidate map, and execute on
  the outer queryset;
- the signature detects a flipped non-pk pk-qualification marker and a directly
  replaced `.filter` callable;
- forward Relay FK `in` generation now retains the list-shaped filter for both
  ordinary and non-pk-`to_field` relations;
- the specification now states the reachable `exclude=True` invariant instead
  of requiring an impossible generated leaf;
- the glossary documents the multiset-selection behavior;
- the live-test guide documents the mixed OR, test-scoped Loan connection, and
  shard execution;
- the relation fixture files now appear in the tree; and
- a real PostgreSQL planner artifact and guarded PostgreSQL regression now
  exist.

## Recommended correction order

1. Preserve consumer relation overrides before Relay conversion; this is a
   direct public-surface behavior loss.
2. Replace the partial mutation tuple with a complete integrity model and gate
   consumer `FilterSet.__init__` overrides.
3. Add the expanded non-pk-`to_field` `in` adapter regression.
4. Make the PostgreSQL artifact generator reproduce the canonical link footer
   and regenerate the tree for all new paths.
5. Reconcile the stale provenance docstring and the over-broad plan/glossary
   claims with the corrected implementation.
6. Remove or explain the tracked SQLite binary change.

The correlated-`EXISTS` classifier and neutral predicate primitive remain the
right architecture. The remaining root issue is still the ownership boundary
between django-filter's mutable/customizable filter objects and the
package-owned correlated invocation.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: GLOSSARY.md#filterset
[part1-plan]: row-preserving-predicates-part1-plan.md
[pg-artifact]: row-preserving-predicates-part1-pg-explain.md
[tree]: TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filter-sets]: ../django_strawberry_framework/filters/sets.py

<!-- tests/ -->
[pg-test]: ../tests/test_predicate_pg_explain.py

<!-- examples/ -->

<!-- scripts/ -->
[pg-capture]: ../scripts/capture_pg_predicate_explain.py

<!-- .venv/ -->

<!-- External -->
