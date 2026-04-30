# Review Feedback: `spec-optimizer_beyond.md`

## Scope reviewed

- `docs/spec-optimizer_beyond.md`

This feedback only covers the current spec text.

## Findings

### 1. B6's audit target is still too broad and will produce false positives on valid hidden relations

Priority: P1

B6 says to walk each reachable model's `model._meta.get_fields()` and check every relation field. That is broader than the GraphQL surface the optimizer actually owns. A reachable `DjangoType` can legitimately hide relations via `Meta.fields`, `Meta.exclude`, or future `OptimizerHint.SKIP`, and those should not be flagged as missing optimization stories. As written, the audit will warn on model relations that are not exposed by the type at all, which makes the startup report noisy and untrustworthy.

Recommended fix:

- narrow the audit to the relation fields exposed by the reachable `DjangoType`, not the full Django model field set
- explicitly say the audit must honor `Meta.fields`, `Meta.exclude`, and future optimizer-hint opt-outs when deciding what is "reachable by the walker"

### 2. B3 still underspecifies alias-safe relation-path matching

Priority: P1

B3 says the resolver can reconstruct its dotted path from `info.path` by walking `.prev` and `snake_case`-ing each segment. That is not enough once aliases enter the query, because `info.path` is a response path, not necessarily the underlying schema field path. A query like `{ allItems { cat: category { name } } }` yields a response-path segment like `cat`, while the optimizer plan is keyed on `category`. If the spec does not call this out explicitly, a straightforward implementation will misclassify planned aliased relations as unplanned.

Recommended fix:

- add an explicit rule that B3 must compare against underlying field names, not response aliases
- either require resolver-side access to the field definition name, or prefer the alternative context-stashed path mapping for alias safety
- add alias-based coverage to the B3 test surface in the spec text

### 3. B8's queryset-state description is factually incomplete for `select_related()`

Priority: P2

B8 says `queryset.query.select_related` is either `False` or a nested `dict`. Django also uses `True` for the wildcard `select_related()` case. If the implementation follows the current spec literally, the diffing logic will mishandle or crash on querysets where the consumer already called bare `.select_related()`. That is exactly the kind of consumer-applied optimization B8 is supposed to coexist with.

Recommended fix:

- update the B8 mechanism section to describe the three real states: `False`, `True`, or nested `dict`
- specify what the optimizer should do when it sees `True` — practically, treat all `select_related` entries as already satisfied and skip select-related deltas

### 4. B2's elision-marker scope is not pinned tightly enough for repeated field names

Priority: P2

B2's pseudo-code uses `mark_fk_id_elided(field.name)`, and the prose says the resolver reads an elision flag from `info.context` at call time. That is underspecified for queries with the same relation name in multiple branches or under multiple root fields. A flat flag keyed only by `field.name` can leak elision state from one branch into another and cause the wrong resolver behavior.

Recommended fix:

- require the elision marker to be keyed by full relation path, not bare field name
- state that the resolver consults the same full-path identity the optimizer used when planning the elision

## Overall assessment

The spec has the right shape and the remaining gaps are mostly about precision, not direction. The main thing to tighten before the next implementation pass is identity: which fields the audit actually owns, which names strictness compares, which queryset states diffing must understand, and which path an elision marker belongs to.
