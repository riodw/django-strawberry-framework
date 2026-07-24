# Sixth adversarial implementation review: row-preserving predicates Part 1

## Verdict

The implementation is converging, and the previous review's concrete behavior defects are
substantially closed:

- unsupported lookups on framework-owned Relay relations now raise a typed
  `ConfigurationError` at generation time while consumer-owned relation overrides retain
  their own lookup semantics;
- empty decoded GlobalID node identifiers now reject consistently through the shared
  decoder, including live scalar, all-empty-list, and mixed-list acceptance coverage;
- relation `isnull` keeps its Boolean input shape and now has schema-level coercion
  coverage;
- the prior mutable-shared-entry attacks now fail loudly in the spellings the tests cover;
- the signature suite now gives behaviorally meaningful rows to the mutable fields that
  can change result semantics and documents the no-op-equivalent fields separately; and
- the supported Python 3.10 / Django 5.2.0 floor remains present in push and pull-request
  CI.

Part 1 is nevertheless **not ready to call architecturally closed**. The new fix introduces
two related authorization blockers and one consumer-compatibility regression:

1. `_PACKAGE_FILTER_DEFAULTS` is not intrinsically package-owned. It snapshots the live,
   mutable `django_filters.filterset.BaseFilterSet.FILTER_DEFAULTS` at import time, so
   consumer or third-party mutations made before that import are reclassified as trusted
   package policy and can mint a routing token.
2. `_family_profile_for` treats every subclass of a registered base as audited. An
   unregistered subclass with additional behavior therefore receives a profile through
   its MRO, contradicting the fail-closed contract.
3. Installing nested `MappingProxyType` objects as the consumer-facing
   `FilterSet.FILTER_DEFAULTS` breaks normal copy/customization behavior inherited from
   django-filter; `copy.deepcopy(FilterSet.FILTER_DEFAULTS)` fails on both Python 3.10 and
   current Python.

The first two combine into a reproducible result-semantics authorization failure: an
application-owned filter class installed in django-filter's global defaults before package
import becomes `origin="framework_default"`, `generation_capable=True`, `eligible=True`,
and token-bearing even though the class is absent from the registry and carries unsigned
behavior.

## Blocker 1 — the “package-owned” baseline can capture consumer policy at import

The central premise of the new ownership fix is stated in
`django_strawberry_framework/filters/sets.py::_PACKAGE_FILTER_DEFAULTS`: the snapshot is a
package-owned, immutable generation-policy baseline. Its source, however, is:

```python
_PACKAGE_FILTER_DEFAULTS = _freeze_filter_defaults(
    filterset.BaseFilterSet.FILTER_DEFAULTS,
)
```

`BaseFilterSet.FILTER_DEFAULTS` is explicitly live, mutable, and process-shared. Freezing
its current contents does not establish who authored those contents; it only prevents
later mutation of the snapshot. Any application, reusable Django app, or initialization
hook that customizes django-filter's defaults before
`django_strawberry_framework.filters.sets` is imported is silently promoted into the
trusted baseline.

That import order is realistic. Installing `django_strawberry_framework` as a Django app
imports the package root, but the package root does not import `filters.sets`; filter
modules can be loaded later while application modules and app initialization have already
run.

### Reproduction

In a fresh process, before importing `django_strawberry_framework.filters.sets`:

```python
from django.db import models
from django_filters import CharFilter, filterset


class ConsumerOrderingCharFilter(CharFilter):
    descending = True

    def filter(self, qs, value):
        return qs.order_by("-pk" if self.descending else "pk")


filterset.BaseFilterSet.FILTER_DEFAULTS[models.TextField][
    "filter_class"
] = ConsumerOrderingCharFilter

from apps.library.models import Book
from django_strawberry_framework.filters.sets import FilterSet


class BookFilter(FilterSet):
    class Meta:
        model = Book
        fields = {"loans__note": ["icontains"]}
```

The current implementation reports:

```text
leaf ConsumerOrderingCharFilter
exact_registry False
origin/capable framework_default True
eligible/token/profile True 2 scalar_lookup
fingerprint before True
fingerprint after class-state mutation True
```

The deep `loans__note` leaf crosses a reverse FK, so it is a row-preserving candidate. The
consumer class is not a registry key, but the MRO matcher gives it the `CharFilter`
`scalar_lookup` profile. Because the mutable upstream entry was captured before package
import, the ownership oracle calls it `framework_default`, the capability gate calls the
class capable, and the snapshot mints a token.

This is observably unsafe, not merely a provenance-label disagreement:

- the original outer invocation of `ConsumerOrderingCharFilter.filter` changes the outer
  queryset ordering;
- the routed invocation applies that ordering only to the correlated inner queryset;
  `Exists` discards subquery ordering, so the outer ordering does not change; and
- mutating the class-level `descending` behavior after the snapshot does not change any
  current fingerprint member. The class, `.filter` descriptor, token, and family profile
  all remain equal, so routing stays authorized while behavior changes.

An `extra`-only pre-import mutation is trusted the same way. For example, replacing the
upstream `TextField` `extra` provider with `lambda field: {"exclude": True}` produces a
leaf with:

```text
exclude True
origin framework_default
generation_capable True
eligible True
token 2
```

That directly disproves the standing invariant that generated candidates never carry
`exclude=True`. Even if a particular exclusion currently happens to be relationally
equivalent inside the correlated root, it is outside the audited and documented Part 1
contract and must not be authorized accidentally.

### Required root-cause correction

Do not derive package ownership from whatever happens to be in a mutable third-party
global at import time.

The durable architecture should separate three concepts:

1. **Package policy:** an independently defined, immutable, normalized table owned by this
   package and reviewed with this package's supported django-filter families.
2. **Effective generation policy:** the mapping the current `FilterSet` class will actually
   give django-filter, including consumer `FILTER_DEFAULTS` and `Meta.filter_overrides`.
3. **Selection provenance:** a frozen generation-time record of which normalized policy
   entry selected the class and extras for this exact field/lookup.

Generation and ownership must consume the same normalized selection record. A difference
between effective policy and package policy is consumer-owned and cannot mint a token,
regardless of whether the difference arrived through:

- a subclass replacement;
- nested mutation;
- mutation of `BaseFilterSet.FILTER_DEFAULTS` before or after package import;
- a stateful `extra` provider; or
- a future django-filter release changing the default entry shape.

Do not solve this by adding another request-time marker. The defect occurs before the
candidate exists: consumer policy is being mislabeled as package policy. Correct the
generation-policy source and provenance boundary.

Required regressions:

- mutate `BaseFilterSet.FILTER_DEFAULTS` **before** importing/reloading the package filter
  module and prove the resulting custom class or `extra` provider is consumer-owned and
  tokenless;
- use a custom filter whose outer invocation changes ordering and prove it is never routed;
- install an `extra` provider that generates `exclude=True` and prove the candidate gate
  refuses it;
- prove pristine package defaults still generate token-bearing candidates; and
- restore all third-party global state in process-isolated tests so this regression cannot
  contaminate neighboring suites.

## Blocker 2 — MRO family matching is an open ancestry allowlist

`django_strawberry_framework/filters/sets.py::_family_profile_for` walks
`type(filter_instance).__mro__` and returns the first registered ancestor. This is useful
for django-filter's generated `ConcreteInFilter` and `ConcreteRangeFilter`, but it is not a
fail-closed family registry.

Any subclass of a registered family is accepted, including a subclass the package has
never audited:

```python
class FutureSemanticCharFilter(CharFilter):
    reverse = True

    def filter(self, qs, value):
        if self.reverse:
            return qs.exclude(**{self.field_name: value})
        return super().filter(qs, value)
```

Current result:

```text
exactly registered False
resolved profile scalar_lookup
```

The exact class is signed in `_CandidateFingerprint.filter_class`, but that only detects a
class swap between build and request. It does not prove that the original class was
audited. Likewise, signing the subclass's `.filter` descriptor proves the method did not
change; it does not sign arbitrary state that the unreviewed method reads.

This matters independently of Blocker 1 because `django-filter>=25.2` has no upper bound. A
future django-filter version can place a new subclass of `CharFilter`,
`ModelMultipleChoiceFilter`, `BaseInFilter`, or another registered ancestor into its
defaults. The current MRO walk will automatically authorize it before this package has
audited its call graph or state.

The existing negative test uses `_UnknownFamilyFilter(Filter)`. That proves only that a
direct descendant of the deliberately unregistered universal `Filter` base fails closed.
It does not test the dangerous case: an unknown descendant of a **registered** base.

### Required root-cause correction

The behavior profile must be minted from a known generation decision, not rediscovered
from arbitrary ancestry.

Recommended shape:

- stable audited families match by exact class;
- package-owned filter classes match by exact class;
- django-filter's dynamic `in` / `range` classes receive a profile at the generation site,
  where the package knows the lookup kind and the exact audited scalar class used to build
  the dynamic class;
- the generated profile travels through deepcopy with the same provenance/token chain;
  and
- an arbitrary subclass of an audited base receives no profile unless explicitly added and
  audited.

If structural recognition remains for dynamic CSV classes, it must validate their exact
MRO and class body rather than grant trust to every descendant of `BaseInFilter` or
`BaseRangeFilter`. A dynamic class that adds a new method, descriptor, or state-bearing
attribute must fail closed.

Required regressions:

- an unregistered subclass of every broad registered category (`CharFilter`,
  `ModelMultipleChoiceFilter`, `BaseInFilter`) resolves to no profile;
- genuine django-filter-generated `ConcreteInFilter` and `ConcreteRangeFilter` instances
  still receive their intended profiles;
- a dynamic subclass with one added behavior member fails closed;
- every exact filter class in the package-owned generation table has an audited profile;
  and
- upgrading django-filter cannot add a routable default class merely through inheritance.

## High 3 — the frozen public `FILTER_DEFAULTS` is not a drop-in django-filter mapping

The implementation installs the nested immutable snapshot directly as
`FilterSet.FILTER_DEFAULTS` and calls it a drop-in replacement because django-filter itself
only shallow-copies and reads the mapping.

That considers only django-filter's internal reader. `FILTER_DEFAULTS` is also an inherited
class customization seam for consumers. The [FilterSet glossary entry][glossary] promises
that, because this class is a `BaseFilterSet` subclass, every django-filter filter,
`FilterMethod`, and form-cleaning primitive carries over. A nested `MappingProxyType`
changes that extension behavior:

```python
import copy

from django_strawberry_framework.filters import FilterSet

copy.deepcopy(FilterSet.FILTER_DEFAULTS)
```

On both the supported Python 3.10 floor and current Python, this raises:

```text
TypeError: cannot pickle 'mappingproxy' object
```

The following formerly ordinary customization forms now also raise:

```python
defaults = dict(FilterSet.FILTER_DEFAULTS)
defaults[models.CharField]["extra"] = custom_extra

FilterSet.FILTER_DEFAULTS[models.CharField] = replacement
```

The first aliases a frozen nested proxy; the second targets the frozen outer proxy. The
tests currently assert these failures as the desired fix, but that converts an ownership
implementation detail into a consumer-visible compatibility break.

The root fix should keep an immutable **private normalized baseline** without forcing the
consumer-facing django-filter mapping itself to be a non-copyable type. The capability
check can compare the effective policy against the immutable normalized baseline and fail
closed on drift. It does not need to make the inherited public mapping a
`MappingProxyType`.

At minimum, the public surface must remain safely cloneable for subclass customization,
and the supported customization spelling must be documented and tested. Given the
package's DRF/django-filter migration contract, preserving normal `dict`/deepcopy behavior
is preferable to documenting a new incompatibility.

Required regressions:

- `copy.deepcopy(FilterSet.FILTER_DEFAULTS)` works on Python 3.10 and current Python;
- the copy can replace one nested entry without mutating the package baseline;
- replacing one entry marks only that entry consumer-owned while untouched entries retain
  their intended framework behavior;
- mutating a consumer copy cannot contaminate another FilterSet; and
- the private package baseline remains immutable and independent of the public copy.

## Medium 4 — `relevant_reads` does not make the semantic audit executable

`_FilterFamilyProfile.relevant_reads` is described as the executable per-family inventory
of runtime reads. In the implementation, however:

- `_fingerprint_of` always constructs one union fingerprint and never consults
  `profile.relevant_reads`;
- `test_family_profiles_declare_valid_read_inventories` checks only that declared names are
  dataclass fields and that every profile includes `_CORE_FAMILY_READS`; and
- adding a new family with only `_CORE_FAMILY_READS` passes that structural test even if
  the new `.filter` implementation reads additional state.

The registry makes **membership** executable, but it does not make the effective-read audit
executable. That is why Blocker 2 can assign `scalar_lookup` to a subclass whose
`descending` or `reverse` state is absent from the fingerprint without any registry test
failing.

The higher-quality shape is for a profile to own a semantic-state extractor (or a tuple of
named extractor functions) that produces its normalized fingerprint contribution. Adding
a family would then require executable extraction logic, not only a frozenset of field
names and prose saying an audit occurred. The common core can stay DRY; each profile adds
only its family-specific state.

At minimum, add a test that the set of reads declared by every profile exactly matches the
state its extractor emits. A one-way subset assertion is too weak to serve as an integrity
boundary.

## Medium 5 — specification and documentation now overstate the fixed guarantees

Several standing statements need correction if the implementation remains in its current
shape:

- The [Part 1 plan][part1-plan] says an unknown or ambiguous family resolves to no profile.
  An unknown subclass of any registered base currently resolves to that ancestor's
  profile.
- The plan calls `_PACKAGE_FILTER_DEFAULTS` package-owned. It is immutable after creation,
  but its initial contents can be consumer-owned because they come from a mutable
  third-party global.
- The [FilterSet glossary entry][glossary] promises django-filter primitives carry over,
  but it does not disclose that `FILTER_DEFAULTS` is now non-mutable and non-deepcopyable.
- The glossary says generated candidates never carry `exclude=True`; a pre-import
  upstream-default customization currently creates an eligible, token-bearing
  `exclude=True` candidate.
- [spec-027][spec-027] now carries the general empty-node-id GlobalID contract, but its
  historical “exactly 14 live tests” statements do not distinguish the original card's 14
  tests from the three later empty-ID acceptance tests added to the same live suite.
- The [live-test README][test-query-readme] describes the row-preserving and GlobalID
  acceptance responsibilities in detail but does not yet mention the new empty-node-id
  rejection contract.

Do not document around Blockers 1 and 2. Correct the architecture first, then update the
plan and glossary to describe the actual final boundary. The spec-027 and live-test README
updates are straightforward bookkeeping after that.

## Missing tests implied by this review

The current additions are strong for the earlier findings, but the new architecture needs
the following adversarial rows:

1. A fresh-process import-order test that mutates django-filter defaults before importing
   package filters.
2. An unknown subclass of a registered family, not only a direct `Filter` subclass.
3. A custom family whose outer behavior changes ordering, proving that accidental routing
   is observably different from the outer invocation.
4. A build-time `exclude=True` candidate refusal.
5. A Python 3.10 `FILTER_DEFAULTS` deepcopy/customization compatibility test.
6. An inverse registry assertion: every package-generation class is explicitly audited,
   and no other class is accepted merely by ancestry.
7. A profile-extractor completeness test if the registry is refactored to own executable
   semantic extraction.

These belong primarily in [package FilterSet tests][test-sets]. Consumer-visible behavior
that can be exposed through the existing fakeshop schema should retain a live HTTP
acceptance companion, following the [live-test tier contract][test-query-readme].

## What is satisfactorily closed

The following earlier findings do not need to remain open:

- [FilterSet.filter_for_lookup][filter-sets] now classifies framework-owned Relay relation
  lookups exhaustively: `exact`, `in`, and `isnull` are the only accepted shapes, while an
  unsupported lookup fails at generation. Consumer-owned overrides are checked first and
  keep their own class.
- [GlobalID decoding][filter-base] now rejects an empty decoded node identifier with
  `GLOBALID_INVALID` before either scalar or multiple predicate construction. The live
  tests cover scalar, all-empty list, and mixed-list index reporting.
- [spec-027][spec-027] is now the normative home for that general GlobalID input rule, so
  the earlier Part 1 scope concern is resolved.
- [Relay relation `isnull` input coverage][test-inputs] verifies Boolean annotation,
  introspection, accepted Boolean coercion, and rejected String coercion.
- The effective `to_field_name` read remains signed from the live built form field.
- The signature suite now distinguishes genuinely behavioral mutations from fields whose
  no-op decision is equivalent on the inner and outer invocations.
- The existing direct reverse-FK, expanded reverse-M2M, Medtrics-shaped mixed `OR`,
  pre-fanned multiset, connection pagination, PostgreSQL, and sharded-database coverage
  remains aligned with the [Part 1 plan][part1-plan] and the
  [live-test README][test-query-readme].

No new result-set defect was found in the currently audited, pristine built-in filter
families themselves. The remaining blockers are at the trust boundary that decides which
families and policies count as pristine.

## Recommended correction order

1. Replace the import-time snapshot of mutable upstream state with an independently owned
   normalized package policy and generation-time selection provenance.
2. Replace open-ended MRO family authorization with exact or generation-stamped profiles;
   preserve dynamic `in`/`range` support explicitly.
3. Restore a copyable consumer-facing `FILTER_DEFAULTS` extension surface while keeping
   the private policy baseline immutable.
4. Make each family profile own executable semantic-state extraction.
5. Add the import-order, unknown-descendant, ordering, exclusion, Python 3.10, and inverse
   registry regressions.
6. Reconcile the Part 1 plan, glossary, spec-027 test-count wording, and live-test README
   with the corrected final behavior.

After those corrections, one final adversarial pass should be enough unless the normalized
policy redesign exposes another consumer customization path.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[pyproject]: ../pyproject.toml

<!-- docs/ -->
[glossary]: GLOSSARY.md#filterset
[part1-plan]: row-preserving-predicates-part1-plan.md

<!-- docs/SPECS/ -->
[spec-027]: SPECS/spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filter-base]: ../django_strawberry_framework/filters/base.py
[filter-sets]: ../django_strawberry_framework/filters/sets.py

<!-- tests/ -->
[test-inputs]: ../tests/filters/test_inputs.py
[test-sets]: ../tests/filters/test_sets.py

<!-- examples/ -->
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
