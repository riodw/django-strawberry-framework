# Review: `django_strawberry_framework/filters/base.py`

Status: verified

Supersedes the stale 0.0.7 artifact (was `Status: verified`); the active
plan box (`review-0_0_9.md:79`) is unchecked. Fresh 0.0.9 review focused on
0.0.8/0.0.9 drift: the spec-031 strategy-aware GlobalID validation trio
(`_target_definition_for` / `_accepted_globalid_type_names` /
`_decode_and_validate_global_id`) and the `edab6806` DRY pass that re-based
`RelatedFilter` onto `RelatedSetTargetMixin`.

## DRY analysis

- None — the 0.0.9 DRY pass already landed every reasonable consolidation in
  this file. Empty-list `FilterMethod` behavior is single-sited in
  `_EmptyListAwareFilterMethod` (base.py:67-82) with `ArrayFilterMethod` /
  `ListFilterMethod` as thin markers (base.py:85-86, 161-162). The
  owner-bind + lazy-target machinery is single-sited in
  `sets_mixins.RelatedSetTargetMixin` and consumed here through the
  family-named thin wrappers `bind_filterset` / `.filterset` /
  `.filterset.setter` (base.py:421-470). Strategy frozensets
  (`MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES`) are imported from
  `types/relay.py:413-414`, not re-spelled. The `ArrayFilter` /
  `ListFilter` `method`-setter pair (base.py:117-122, 174-179) is a
  deliberate two-line sibling whose only divergence is the `*Method`
  class it installs — extracting it would re-hide the per-class method
  type behind an indirection for no net line saving.

## High:

None.

## Medium:

None.

## Low:

### GLOSSARY `RelatedFilter` over-claims the failure mode of unqualified-name resolution (cross-file; forward to folder pass)

`docs/GLOSSARY.md:994` (the `RelatedFilter` entry) states the
unqualified-name form will "fail loud with a `ConfigurationError` naming
both attempts if neither resolves." The actual resolution path is
`RelatedFilter.filterset` (base.py:457-466) -> `_resolved_target`
(`sets_mixins.py:176-183`) -> `LazyRelatedClassMixin.resolve_lazy_class`
(`sets_mixins.py:113-139`). On the second attempt, that code calls
`import_string(f"{bound_class.__module__}.{class_ref}")` (sets_mixins.py:134-135)
and lets the **raw `ImportError`** propagate — it is NOT rewrapped into a
`ConfigurationError`, and the surfaced error names only the second
(module-prefixed) path, not "both attempts." This is the same stale-prose
issue already recorded against the sibling `RelatedOrder` entry
(GLOSSARY:1004) in worker-1 memory; it is duplicated verbatim on the
`RelatedFilter` entry.

This is a cross-file GLOSSARY prose defect on a public-contract symbol, but
the fix lives in `docs/GLOSSARY.md`, not in `filters/base.py`. Per the
folder-pass discipline, it is forwarded to `rev-filters.md` rather than
fixed here (a GLOSSARY edit would also disqualify this file's no-source-edit
shape). Severity is Low rather than Medium because the prose mis-attributes
the *failure exception type and message detail* of a rarely-hit
mis-configuration branch (an unqualified name that resolves against neither
the bare path nor the binding module) — it does not misdescribe any
success-path contract a consumer relies on.

Verbatim replacement text for the offending sentence in GLOSSARY:994
(Worker 2 / folder pass lifts directly):

> The unqualified-name form is resolved lazily via Layer 2's module-fallback resolution — try as an absolute import path first, fall back to prepending the binding `FilterSet`'s `__module__`; if that second attempt also fails, the raw `ImportError` from the module-prefixed path propagates unchanged (the resolver does not rewrap it into a [`ConfigurationError`](#configurationerror), and the error names only the module-prefixed path, not both attempts).

Forwarded to: `docs/review/rev-filters.md` (filters folder pass). Note the
identical correction is already owed against the `RelatedOrder` entry
(GLOSSARY:1004) per prior-cycle worker memory — the folder/orders pass
should reconcile both in one sweep so the two sibling entries stay parallel.

## What looks solid

### DRY recap

- **Existing patterns reused.** Empty-list `FilterMethod` semantics single-sited
  in `_EmptyListAwareFilterMethod` (base.py:67-82); owner-bind / lazy-target
  resolution single-sited in `sets_mixins.RelatedSetTargetMixin`, consumed via
  thin family-named wrappers (base.py:393-394, 421-470); strategy frozensets
  imported from `types/relay.py:413-414`; the GlobalID decode/validate path
  is shared by both `GlobalIDFilter` and `GlobalIDMultipleChoiceFilter`
  through the module-level `_decode_and_validate_global_id` (base.py:261-294).
- **New helpers considered.** The `ArrayFilter` / `ListFilter` `method`-setter
  pair and the two `*Method` markers were considered for a single
  parameterized helper and rejected: the only varying token is the installed
  `FilterMethod` subclass, and the current two-line setters read more directly
  than a factory would. The `_target_definition_for` own-PK vs relation split
  is deliberately single-sited so `_accepted_globalid_type_names` consumes
  exactly one definition (spec-031 Decision 13) — not a duplication.
- **Duplication risk in the current file.** The `_target_attr` / `_owner_attr`
  string slots (base.py:393-394) mirror the order twin's
  `("_orderset", "bound_orderset")`; this is intentional per-family
  parameterization of the shared mixin, not a literal to hoist (the two
  families bind different attribute names by design).

### Other positives

- **Strategy-aware acceptance is internally consistent.** `_accepted_globalid_type_names`
  (base.py:250-258) maps `model`->label, `type`->type-name, `type+model`->both
  (a two-element set, so `expected` renders `"<a> or <b>"` at base.py:290), and
  `callable`/`custom`/absent-strategy/unresolved-target all fall through to
  `accepted or None` -> `None`, which skips the guard (node-id-only fallback).
  Verified against the frozensets at `types/relay.py:413-414` and the
  `effective_globalid_strategy: str | None` field at `types/definition.py:173`.
- **Defense-in-depth, never the error oracle.** The filter validation deliberately
  falls back to node-id-only for unknown/absent strategy and unbound owner
  rather than raising — the uniform-error contract is decode's job. The
  decode itself runs (`relay.GlobalID.from_id`) before the type-name guard,
  and `isinstance(value, relay.GlobalID)` lets an already-decoded GlobalID
  through without re-decoding (base.py:285). Both `GlobalIDFilter.filter` and
  the multi-choice variant short-circuit `value is None` to the unfiltered
  `super().filter` before any decode (base.py:318-319, 362-363).
- **Empty-list contracts are correct and per-shape.** `ArrayFilter.filter`'s
  `value in EMPTY_VALUES and value != []` (base.py:126) keeps `[]` as a real
  value (membership uses `==` against the `EMPTY_VALUES` tuple, so the
  unhashable `[]` is safe) while still short-circuiting `None`/`""`/`()`;
  `ListFilter.filter` routes `[]` to `qs.none()` (or `qs` when `exclude=True`)
  before delegating to `super().filter` (base.py:183-185). The custom-`method`
  setters install the empty-list-aware `FilterMethod` only when a `method=` is
  actually supplied (`if value is not None`, base.py:121, 178).
- **`RelatedFilter` lazy-resolution + guard composition.** The three documented
  target shapes (class / absolute import path / unqualified name) all funnel
  through `resolve_lazy_class`; the `lookups=` kwarg guard runs *before*
  `super().__init__` (base.py:412-418) precisely because
  `django_filters.Filter.__init__` would otherwise silently absorb it into
  `self.extra` — a sound order-of-operations choice. `_has_explicit_queryset`
  is genuinely consumed downstream (`filters/sets.py:1556`), so the recorded
  intent is load-bearing, not dead state. `get_queryset` preserves an explicit
  queryset verbatim and only auto-derives from `target._meta.model` when
  `super().get_queryset` returns `None` (base.py:480-486), with nested
  `getattr(getattr(...))` guarding a missing `_meta`/`model`.
- **Idempotent bind is correctly documented as a deliberate silent no-op**, with
  the strict cross-owner mismatch deferred to finalize-time
  (`types/finalizer.py::_bind_filterset_owner`) and the unqualified-string
  resolution-scope caveat spelled out in the `bind_filterset` docstring
  (base.py:440-451) — a real hazard, honestly surfaced rather than hidden.
- **Import-direction comment is load-bearing and accurate.** The module-top
  `filters/base.py -> types/relay.py` import (base.py:47) is justified inline
  (base.py:41-46): `types/relay.py` reaches into `filters`/`registry` only via
  in-function imports, so no load cycle closes. The `if TYPE_CHECKING` block
  (base.py:49-53) keeps `HttpRequest` / `BaseFilterSet` / `DjangoTypeDefinition`
  out of runtime import cost.

### Summary

Clean 0.0.9 review. The 0.0.8/0.0.9 drift (spec-031 strategy-aware GlobalID
validation and the `RelatedSetTargetMixin` DRY re-base) is correctly
implemented and faithfully documented in source — encode/decode/filter all
agree on one strategy contract, the empty-list filter shapes are
per-primitive and correct, and `RelatedFilter`'s lazy resolution + guard
composition are sound. No High, no Medium. The single finding is a cross-file
GLOSSARY Low: the `RelatedFilter` entry (GLOSSARY:994) over-claims a
`ConfigurationError`-rewrap "naming both attempts" where the resolver
actually lets a raw `ImportError` propagate naming only the second path —
forwarded with verbatim replacement text to `rev-filters.md` (and flagged as
parallel to the same already-known over-claim on the `RelatedOrder` entry).
Because that fix is a GLOSSARY edit owned by the folder pass and this file
needs no source/test/GLOSSARY edit, this is a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 265 files left unchanged.
- `uv run ruff check --fix .` — pass, all checks passed (no fixes applied).

### Notes for Worker 3
- The single Low is a cross-file GLOSSARY prose defect (GLOSSARY:994,
  `RelatedFilter` entry) forwarded to the filters folder pass `rev-filters.md`
  with verbatim replacement text. It is NOT a local edit to `filters/base.py`
  and is NOT a GLOSSARY-only fix executed in this cycle — per the dispatch
  constraint it is recorded-and-forwarded only.
- No GLOSSARY-only fix in scope for this artifact (a GLOSSARY edit would
  disqualify the no-source-edit shape; the edit is owned by the folder pass).
- No High/Medium. No deferred-with-trigger findings. No DRY act-now items.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

Source comments and docstrings reviewed alongside logic: all accurate against
the current implementation. The module docstring, the spec-027/spec-031
pinpoint citations, the empty-list contract docstrings on `ArrayFilter` /
`ListFilter`, the `bind_filterset` silent-no-op + unqualified-string caveat,
and the import-direction comment block all match behavior. No source
comment/docstring edits warranted.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source change was made (AGENTS.md: "Do not update
CHANGELOG.md unless explicitly instructed"), and the active plan
(`review-0_0_9.md`) records no changelog obligation for this item. The single
finding is a forwarded cross-file GLOSSARY prose correction owned by the
folder pass, not a behavior change.

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5). Baseline `0872a20f` diff for
`django_strawberry_framework/filters/base.py` is EMPTY (true no-op). High 0 /
Medium 0; the single Low is the cross-file GLOSSARY:994 `RelatedFilter`
over-claim, correctly forwarded with verbatim replacement text — not a
`base.py` edit.

Independently re-derived the load-bearing claim that keeps this shape #5
rather than forcing a source fix: the lone Low asserts the resolver lets a
**raw `ImportError`** propagate (naming only the module-prefixed second
attempt) and that the `ConfigurationError` rewrap lives a layer up. Confirmed
against source rather than the artifact:

- `sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class`
  (`sets_mixins.py` #"return import_string(path)") — second attempt calls
  `import_string(f"{bound_class.__module__}.{class_ref}")` and lets the raw
  `ImportError` propagate (`except ImportError:` re-attempts, then on falsy
  `bound_class` `raise`s the ORIGINAL unchanged; the second attempt is not
  wrapped). The method's own docstring even states "the original
  `ImportError` propagates unchanged." So `base.py` is NOT the raiser of a
  `ConfigurationError` "naming both attempts," and contains no resolution
  code to edit — `RelatedFilter.filterset` (base.py
  #"return self._resolved_target()") delegates to the mixin.
- The rewrap lives in `types/finalizer.py::_finalize_set_family`
  (`finalizer.py` #"references an unresolved") — `except ImportError as exc:`
  -> `raise ConfigurationError(... {exc}) from exc`, where `{exc}` is the raw
  ImportError message = the resolved (module-prefixed) path only, never both
  attempts. The orderset twin's docstring (`finalizer.py` #"is rewrapped as")
  states the same. This matches the dispatch's known fact exactly and is the
  parallel of the already-recorded `RelatedOrder` (GLOSSARY:1004) finding.

`base.py` itself carries no GLOSSARY prose and no resolution logic, so the
GLOSSARY:994 correction needs ZERO `base.py` source/test edit. Shape #5 holds.
All other `What looks solid` claims spot-checked and accurate (strategy-aware
`_accepted_globalid_type_names` against `types/relay.py` frozensets; `lookups=`
guard ahead of `super().__init__`; idempotent `_bind_owner` no-op;
node-id-only defense-in-depth fallback).

### DRY findings disposition
DRY analysis = None; the 0.0.9 `edab6806` re-base onto `RelatedSetTargetMixin`
already single-sited the owner-bind / lazy-target machinery, consumed here via
the thin family-named wrappers (`bind_filterset` / `.filterset` /
`get_queryset`). Confirmed the wrappers delegate (`_bind_owner` /
`_resolved_target` / `_set_target`) rather than re-spelling. No act-now item.

### Temp test verification
- None. The verification was settled by reading source (sets_mixins.py +
  finalizer.py rewrap sites) — no behavioral probe needed for a no-op cycle
  whose sole finding is cross-file standing prose.
- Disposition: n/a.

### Cross-file forward
The GLOSSARY:994 `RelatedFilter` over-claim is recorded in THIS artifact with
verbatim replacement text and explicitly forwarded to the filters folder pass
`docs/review/rev-filters.md`, paired with the parallel `RelatedOrder`
(GLOSSARY:1004) entry per prior-cycle memory. The forwarding act this cycle
owns — recording the finding + verbatim text + naming the destination — is
present and correct. (Note: the closed folder pass `rev-filters.md`
[`Status: verified`, `[x]` at review-0_0_9.md:83] consolidated its GLOSSARY
finding as the 22+-symbol coverage gap routed to the project pass and did not
itself land this RelatedFilter:994 ImportError-prose correction; that is a
folder-pass standing-prose debt, NOT a `filters/base.py` cycle defect — it
forces no source change here and does not disqualify shape #5.)

### Sibling-cycle attribution
Owned-paths diff stat (`git diff --stat 0872a20f -- django_strawberry_framework/
tests/ docs/GLOSSARY.md CHANGELOG.md`) carries NO `filters/base.py` hunk. The
dirty hunks attribute to closed sibling cycles:
- `conf.py` -> `rev-conf.md` (verified, `[x]` review-0_0_9.md:70).
- `exceptions.py` -> `rev-exceptions.md` (verified, `[x]` :72).
- `list_field.py` -> `rev-list_field.md` (verified, `[x]` :73).
- `docs/GLOSSARY.md` 1-line hunk = the `DjangoConnection` entry ->
  `rev-connection.md` (verified, `[x]` :71).
Deleted root `feedback2.md` / `feedback3.md` = AGENTS.md #33 concurrent-
maintainer work, left untouched. Untracked `rev-connection.md` /
`rev-relay.md` / `review-0_0_9.md` are new artifacts, not source.
CHANGELOG.md diff empty; changelog disposition "Not warranted" cites both
AGENTS.md and the active plan's silence. Ruff format-check ("already
formatted") + check ("All checks passed!") on `filters/base.py` pass.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
`filters/base.py` box at `docs/review/review-0_0_9.md`.

---

## Iteration log

_None yet._
