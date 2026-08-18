# Rationale: spec-017 — Deferred scalar conversions (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-017-deferred_scalars-0_0_6.md`][spec-017]. The spec is the contract and states only what holds at `HEAD`; everything that explains **how it got there** lives here: ten numbered revisions of review feedback, the alternatives each Decision rejected, the thirteen risks and their preferred answers, every claim the spec once made and may no longer make, and the three later cards that reshaped what this one landed without ever touching the spec.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass.

## Provenance of this record

**This pass performed a MOVE, not a reconstruction.** [`spec-016`][spec-016-rationale]'s companion had to be reconstructed because that spec carried no deliberative layer to cut; [`spec-015`][spec-015-rationale]'s was a genuine move. Spec-017 is squarely a move, and it carried the larger deliberative layer of the two: a 39-line `Revision history` block enumerating ten review rounds, per-Decision "why the alternative lost" argument paragraphs, a thirteen-bullet `## Risks and open questions` section, and a Slice 6 that reproduced two whole KANBAN card bodies verbatim. Text marked **Moved** below was **cut** out of the spec, not copied: it exists here and nowhere else.

**Measured byte counts, both with `wc -c` at this working tree, re-measured at the close of the MF-3 correction pass rather than carried forward from R1:**

| File | Before the R1 move | At close of the MF-3 correction |
|---|---|---|
| `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` | 84,488 | 62,804 |
| `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md` | 0 (did not exist) | 44,338 |

`HEAD` at the time of the pass is `acaa6b833d836aa02487eb14a57eb1c98e93354e`. The package is at `0.0.14`; this card shipped at `0.0.6`.

**Moved** — cut from the spec by this pass, and now only here:

- the whole `Revision history (kept inline so the spec is self-contained)` block, all ten numbered revisions with their H/M/L sub-items and polish paragraphs (39 lines);
- the whole `## Risks and open questions` section, all thirteen bullets;
- the whole `## Current state` section, which described the pre-card baseline (`No BigInt symbol exists yet`);
- Decision 1's three "Why the strict parser / Why the strict serializer / Why the deprecation suppression" argument paragraphs;
- Decision 5's four-bullet "Why reject `choices` rather than ignore" list;
- Decision 6's migration-contract deliberation and its whole "Recommended starting point" paragraph;
- Slice 6's "don't do the NNN renumber" parenthetical, its two verbatim KANBAN card bodies, and the archive-time card-body-stripping instruction;
- Slice 5's "controlled inconsistency" framing of the version-string gap.

**Kept in the spec deliberately, against the pull of this move.** [`worker-1.md`][worker-1]'s carve-out for implementation-relevant rationale is load-bearing here and four passages exercised it:

- The parser's reject-rather-than-coerce reasoning (`bool` is checked *before* `int` because `bool` subclasses `int`; `int(1.9) == 1` truncates silently) stays in Decision 1, because a builder who never reads it writes `parse_value=int` and the ordering bug comes back.
- The serializer's symmetry reasoning stays for the same reason: without it, `serialize=str` looks like a simplification rather than a contract violation.
- The `_field_label` / `_field_has_choices` note stays in Decision 2, because a builder who interpolates `field.model.__name__` directly reintroduces the hostile-descriptor escape those helpers exist to close.
- The `force_nullable`-unset recursion note stays in Decision 2, because threading the override into the `base_field` call is the natural-looking thing to do and is wrong.

**Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the current contract falsifies them: the `Status: draft (revision 10, post-feedback2 re-review)` line; the `## Current state` claim that `SCALAR_MAP` is a `dict[type[models.Field], type]` and that `PositiveBigIntegerField: int` is the live entry; Decision 1's whole `with warnings.catch_warnings():` block and its eleven-line explanatory comment; Decision 4's two `_resolve_*_field()` function bodies; Decision 7's four `_resolve_*_field` helper-resolver test bodies; Slice 6's instruction to move `DONE-017-0.0.6` to `DONE-017-0.0.6`; and every carrier of the claim that `BigAutoField` has "no current-day recourse". Each is recorded below as a claim the spec may no longer make, and none survives anywhere as live spec text - a state reached in two passes, not one: see the `BigAutoField` sub-entry under Decision 1.

**Glossary anchors: sixteen terms, sixteen anchors, all still linked.** Two terms lost their only carrier to this move — `strawberry_config` (carried only by the revision-10 M1 item) and `Upload` (carried only by Decision 6's "Recommended starting point" paragraph). Both were re-homed in reconciled prose: `[strawberry_config][glossary-strawberry-config]` now sits in the rewritten Decision 6, and `[Upload][glossary-upload-scalar]` in `## Out of scope`. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-017-deferred_scalars-0_0_6.md` exits 0 after the rewrite with `OK: 16 terms`.

## What the card actually did, and what later cards did to it

`DONE-017-0.0.6` shipped in `0.0.6` on 2026-05-19 (`CHANGELOG.md #"## [0.0.6] - 2026-05-19"`). Three later changes reshaped what it landed, none of which touched this spec:

| Change | Date | What it changed |
|---|---|---|
| `DONE-025-0.0.7` ([`spec-025-scalar_map_helper-0_0_7.md`][spec-025]) | 2026 | Deleted the `warnings.catch_warnings()` suppression block; redefined `BigInt` as a bare `NewType` plus a separate `_BIGINT_SCALAR_DEFINITION` registered through `_PACKAGE_SCALAR_MAP` and the public `strawberry_config()` factory. Exactly the migration spec-017 roadmapped. |
| commit `17995323` | 2026-07-08 | Replaced `converters.py`'s two hand-rolled `_resolve_array_field()` / `_resolve_hstore_field()` helpers with `utils/imports.py::import_attr_if_importable`, and removed the four helper-resolver tests in the same commit that expanded `tests/utils/test_imports.py`. |
| `DONE-029-0.0.9` ([`spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] Decision 7) | 2026 | Gave `convert_scalar` its keyword-only `force_nullable` tri-state, so `field.null` became `effective_null` at every widening site, with the `ArrayField` recursion left `force_nullable`-unset. |

Two further changes affected the spec's surface without changing its contract: commit `62ae8404` (2026-08-16, "Validate generated GraphQL names and guard type diagnostics") introduced `_field_label` / `_field_has_choices`, and an undated live-first migration promoted nine schema-execution tests to `examples/fakeshop/test_query/test_scalars_api.py`.

### Nothing was skipped in the code

The load-bearing half of this cycle. Every item in the spec's `## Slice checklist`, `## Goals`, `## User-facing API`, `## Test plan`, and `## Definition of done` was walked, and **no item was found that was never shipped.** The full disposition table lived in this cycle's R1 artifact, deleted at closeout with the rest of the per-cycle round records and recoverable from git history at commit `172a1ab1`; the result it establishes is stated above and needs no lookup. Two claims needed more than a grep, and both were re-derived rather than accepted:

- **The nine promoted schema-execution tests.** Each of the nine names the spec pins is absent from the tree under its own name (`grep -rn "def <name>"` over `tests/` and `examples/` returns nothing for all nine). Each was matched, per test, to a live-tier assertion pinning the same contract, and every one of the nine has one. Three of the live tests name the migration in their own docstrings. Not one is a coverage loss.
- **The four helper-resolver tests.** Both branches the deleted tests covered are covered at the shared helper — `tests/utils/test_imports.py::test_import_attr_if_importable_returns_the_attribute_on_an_importable_module` (importable) and `::test_import_attr_if_importable_returns_none_when_the_module_is_unimportable` (unimportable, via the `sys.modules[name] = None` sentinel the spec itself named). A third test, `::test_import_attr_if_importable_raises_when_importable_module_lacks_the_attr`, covers a branch the spec's hand-rolled helpers never had. Coverage went up, not down. `git show 17995323` proves the deletion and the expansion landed in one commit.

## Entries keyed to the spec

### The `Status:` line

**Moved / deleted.** The line read `Status: draft (revision 10, post-feedback2 re-review).` — a chronology in the header of a spec whose card is `Done`. Deleted, not moved: the revision count is recoverable from this file, and "draft" was false the moment `0.0.6` cut. Replaced with `Status: shipped in 0.0.6.` plus a one-line pointer to this file.

### `## Current state`

**Moved.** The whole section. It described the pre-card baseline — a `dict[type[models.Field], type]` `SCALAR_MAP`, three TODO blocks, `PositiveBigIntegerField: int` called "technically incorrect", and the three "does not exist yet" sentences. Every sentence in it is now false, and a reader applying it to `HEAD` would conclude the card never shipped. Recorded here for what it is: a snapshot of `0.0.5`.

**Claims the spec may no longer make:** that `SCALAR_MAP`'s declared value type is `type` (it is `Any`, per Decision 8, shipped); that `PositiveBigIntegerField` maps to `int` (it maps to `BigInt`); that no `BigInt` symbol, no `scalars.py`, and no `tests/test_scalars.py` exist (all three exist).

### `Revision history`, revisions 1-10

**Moved.** The entire block. `docs/builder/BUILD.md` `## Spec rationale extraction` is explicit that the spec never narrates its own history, and this was the purest possible instance: ten numbered rounds of "H1 / M2 / L3 said X, so we changed Y", requiring a reader to apply a chronology to reconstruct what is currently true.

The full text is not reproduced verbatim here; what a reviewer needs is the *decision-keyed* residue, which is distributed through the entries below. The load-bearing content of each round, keyed to what it settled:

- **Rev 1** — initial draft.
- **Rev 2** — HStore targets `JSON` rather than a dedicated scalar (Decision 5); sentinel-guarded `isinstance` over `SCALAR_MAP` registration for the postgres types (Decision 4); fake-field test doubles rather than a postgres driver in dev deps (Decision 7); the GraphQL 32-bit `Int` boundary promoted over JavaScript's 53-bit limit as the *primary* driver for `BigInt` (Decision 1); `PositiveBigIntegerField` mapped to `BigInt` (Decision 1); `SCALAR_MAP` value type widened to `Any` (Decision 8); a schema-execution test required for every public mapping (Decision 7).
- **Rev 3** — `_FakeArrayField` metadata propagation (Decision 7); `BigAutoField` recourse sequenced behind the sibling override card; the overflow failure respecified as an observable `GraphQLError` shape rather than an internal exception type; `BigInt` redefined using `NewType` — **later proven insufficient**, see rev 4.
- **Rev 4** — the Strawberry deprecation accepted for `0.0.6`; the strict parser introduced; the version bump expanded from a quartet to a quintet.
- **Rev 5** — the parser regex tightened to `^(0|-?[1-9][0-9]*)$`, rejecting `"1_000"`, `"+1"`, `"１２"`, `"01"`, `"-0"`; the float-rejection sentence corrected — the bug is `int(1.9) == 1` silently truncating, not a type error.
- **Rev 6** — `managed = False` and the explicit `monkeypatch.setattr(converters, "_*_FIELD_CLS", ...)` ordering pinned in Decision 7; a redundant inner `_ARRAY_FIELD_CLS is not None` check removed; outer `choices` on `ArrayField` rejected; the `T | None` hedge for `NewType` dropped after verifying Python 3.10+; the original Slice 5 split into Slice 5 (version quintet) and Slice 6 (docs), making six slices.
- **Rev 7** — seven structural changes, three of which the current contract has since superseded. See the Decision 1 and Decision 6 entries below.
- **Rev 8** — three structural fixes: HStore outer-`choices` rejection given explicit pseudocode (Decision 5); the deprecation regression test moved from `importlib.reload` to subprocess isolation (Decision 7 — the *only* rev-7-through-10 change that survives verbatim at `HEAD`); the false claim that `tests/types/conftest.py` provides the autouse `registry.clear()` fixture corrected — no such file exists, each test file declares its own.
- **Rev 9** — the "renumber `TODO-ALPHA-020` through `044`" option removed entirely (see the Slice 6 entry); Decision 6's "Committed architectural direction" softened to "Recommended starting point"; the `BigInt` import smoke test softened to `BigInt is not None`, dropping an `isinstance(BigInt, strawberry.types.scalar.ScalarWrapper)` assertion because `ScalarWrapper` is an undocumented internal Strawberry path. **That softening turned out to be correct for a reason rev 9 did not know:** `DONE-025-0.0.7` made `BigInt` a bare `NewType`, so the dropped assertion would have failed. The test's current body still reads `assert BigInt is not None`.
- **Rev 10** — a separate reviewer's pass on rev 8. One rendering bug (an inner ` ```python ` fence closing an outer ` ```markdown ` fence prematurely — fixed by switching the outer to four backticks); `extra_extensions=` removed from the recommended factory signature because Strawberry extensions go to `strawberry.Schema(..., extensions=[...])`, not into `StrawberryConfig` (a judgement the shipped `strawberry_config()` signature vindicates — it has no `extra_extensions`); two internal contradictions in the follow-up card body resolved; a stale test-plan reference to the pre-subprocess deprecation mechanism corrected; the HStore outer-`choices` policy propagated to Goals / Non-goals / the API table; the `managed = False` rationale corrected after the reviewer verified locally that bare `models.Field` subclasses do not trigger `Model.check()` warnings regardless of `managed`.

### Decision 1 — `BigInt` wire format and target fields

**Alternatives rejected, and why each lost:**

- **`parse_value=int`.** Lost because `int(True) == 1`, `int(False) == 0`, and `int(1.9) == 1` — the last is a silent truncation, the worst failure mode available to a scalar. (The *ordering* consequence — check `bool` before `int` — was kept in the spec, because it changes how the parser is written.)
- **`serialize=str`.** Lost because it accepts `True`, `1.9`, `Decimal(...)`, and arbitrary objects and stringifies them, so a schema could emit values its own parser rejects. Symmetric strictness was made a public-scalar discipline rule.
- **A permissive regex, or plain `int(str)`.** Lost on predictability: the shipped regex is deliberately *narrower* than `int(str)`, rejecting `"1_000"` (PEP 515), `"+1"`, `"01"`, `"-0"`, and Unicode decimal digits. Leniency was traded away on purpose.
- **Int64 range enforcement on the scalar.** Rejected as a separate concern; `BigInt` is arbitrary-precision and a consumer wanting a hard 64-bit cap validates in their resolver. A `BigInt64` variant was left to a future card if real demand appeared.
- **Mapping `BigAutoField` to `BigInt`.** Rejected for PK wire-format stability.

**Changes this decision has undergone:**

- **Rev 3** redefined `BigInt` using `NewType` rather than `strawberry.scalar(int, ...)` — and rev 4 proved that insufficient, because `strawberry.scalar(NewType(...))` emits the same `DeprecationWarning` as `strawberry.scalar(int, ...)`.
- **Rev 7 (B1)** wrapped the definition in `warnings.catch_warnings()` + `filterwarnings("ignore", message="Passing a class to strawberry.scalar", category=DeprecationWarning)`. Before that fix, importing `django_strawberry_framework` leaked the warning to every consumer, and under `-W error::DeprecationWarning` the import failed outright. Rev 6's `test_bigint_scalar_definition_emits_strawberry_deprecation_warning` (which *asserted the warning*) was replaced with `test_package_import_does_not_emit_strawberry_deprecation_warning`.
- **Rev 7 (B2)** added `_serialize_bigint` replacing `serialize=str`, with three unit tests and one schema-execution test.
- **Rev 7 (H2)** added `test_bigint_parses_python_zero` and `test_bigint_parses_signed_int64_max_string`, and replaced "sized for 64-bit values" with "typically used to map Django's 64-bit integer fields" — the scalar is arbitrary-precision but sized in practice by its source columns.
- **`DONE-025-0.0.7` deleted the suppression.** At `HEAD`, `django_strawberry_framework/scalars.py` defines `BigInt = NewType("BigInt", int)` and a separate `_BIGINT_SCALAR_DEFINITION` built from the `name=`-only `strawberry.scalar(...)` overload (the `cls is None and name is not None` branch), registered through `_PACKAGE_SCALAR_MAP`. No warning is emitted, so nothing needs suppressing.
- **Later hardening** (commit `62ae8404` and siblings) added `int.__int__(value)` / `str.__str__(value)` normalization inside the parser and serializer, so a hostile `int` / `str` subclass cannot alter the accepted value or replace the scalar's `ValueError` contract, and routed the error text through `_safe_arg_repr` / `_safe_type_name`.

**The claim this decision may no longer make, moved verbatim so it is unmistakable:**

> Why the deprecation suppression: Strawberry's class-direct-to-`scalar()` `DeprecationWarning` is an internal Strawberry concern about how the scalar is defined. The consumer-facing `BigInt` symbol and its wire behavior are unaffected. Letting the warning escape would mean every consumer importing `django_strawberry_framework` (even those who never use `BigInt`) sees the warning, and consumers running under `-W error::DeprecationWarning` cannot import the package at all. Tight scoping at the definition site keeps the public surface clean.

The *goal* survives (a clean import surface); the *mechanism* does not. There is no suppression block, and there is no `import warnings` in `scalars.py`.

**A second claim this decision may no longer make: `BigAutoField` has "no current-day consumer recourse".** The Target-Django-fields bullet read `No current-day consumer recourse for the 2**31 boundary - wait for [Scalar field override semantics]`. It was false on the day `0.0.6` shipped: the sibling card `DONE-019-0.0.6` landed consumer annotation overrides in the same release, so the recourse was never a future thing to wait for. The mapping itself is unchanged and correct - `BigAutoField` stays `int` for PK wire-format stability - and only the "no recourse / wait for" clause was false.

**The claim occupied four sites, and closing three of them is what let the fourth survive.** The population, and which pass closed each:

| Site | Closed by |
|---|---|
| `## Non-goals`, the `BigAutoField` bullet | R1 |
| `## Edge cases and constraints`, the `BigAutoField` bullet | R1 |
| `## Risks and open questions`, the `BigAutoField` bullet | R1 (the whole section was cut) |
| **Decision 1, "Target Django fields"** | **the final test-run gate, as finding MF-3** |

R1 fixed the sites it had read and did not establish the population first. The correct method, and the one used to close MF-3, is [`docs/builder/BUILD.md`][build] `## Claims are proven mechanically, never accepted on prose`: search the shortest distinctive token and count **occurrences**, not matching lines. The population-defining token `BigAutoField` appears 7 times in the spec, and all seven have been read and dispositioned; the false clause's own distinctive phrases, `no current-day` and `wait for`, now appear 0 times each, which is what proves it retired rather than merely reworded at the sites the first pass happened to read. (`recourse` looked like a corroborating token and is not: it is shared with `Meta.exclude`'s unrelated unsupported-field recourse, and the `## Edge cases` carrier does not use the word at all.) The three surviving `BigAutoField` mentions that carry no recourse claim are the verbatim `docs/GLOSSARY.md` entry-text drop-in in Slice 6 (`not BigAutoField`, a scope statement that must stay character-identical to the shipped glossary entry), the `## User-facing API` table row (`int` (unchanged), preserved for PK wire-format stability), and the `## Out of scope` bullet (`BigAutoField -> BigInt`, still out of scope at `HEAD` - `converters.py #"models.BigAutoField: int,"`). A fourth mention, in `## Key glossary references`, described the mapping as a "deferral [that] depends on that contract"; the final-gate pass reworded it, because a deferral already discharged is a recourse, not a dependency.

### Decision 2 — `ArrayField` dimensionality cap and outer-`choices` rejection

**Alternatives rejected:** multi-dimensional `ArrayField` support (rejected as scope; lift in a future card if needed); silently ignoring outer `choices` (rejected — loud over silent, see the Decision 5 entry for the fuller argument, which the two decisions share).

**Changes this decision has undergone:**

- **Rev 6** added the outer-`choices` rejection, which the original draft did not have.
- **`DONE-029-0.0.9`** replaced `field.null` with `effective_null` at the widening site, and left the recursive `base_field` call `force_nullable`-unset. The unset-recursion choice is a real design decision, not an omission, so it stayed in the spec.
- **Commit `62ae8404`** replaced the `f"{field.model.__name__}.{field.name}"` interpolation with `_field_label(field)` and the bare `if field.choices:` truth test with `_field_has_choices(field)`, closing an escape where a hostile field descriptor's exception surfaced as something other than a `ConfigurationError`.

**The claim this decision may no longer make:** that the error messages interpolate `field.model.__name__` and `field.name` directly, and that `choices` is tested as a bare attribute truth value. The rendered message text is unchanged; the way it is built is not.

### Decision 3 — `JSONField` target type

No deliberation to move; the decision is one sentence and has not changed.

### Decision 4 — soft import via module-level sentinels

**Alternatives rejected:** adding a postgres driver to dev dependencies (rejected — the package must import cleanly without one); registering `ArrayField` / `HStoreField` in `SCALAR_MAP` (rejected — the sentinel branches must run *before* the MRO walk so a `models.Field` test double cannot accidentally match a parent entry).

**Changes this decision has undergone.** Commit `17995323` (2026-07-08) deleted both `_resolve_array_field()` and `_resolve_hstore_field()` and routed the sentinels through `django_strawberry_framework/utils/imports.py::import_attr_if_importable`, the package's single optional-import owner (documented as such by [`spec-041-channels_router-0_0_14.md`][spec-041]). The shared helper is *stricter* than what it replaced: the hand-rolled helpers returned the class or `None`, while the helper's `getattr` has no default, so an importable-but-incomplete `django.contrib.postgres.fields` now raises `AttributeError` instead of degrading to `None`.

**The claim this decision may no longer make:** that `_resolve_array_field()` and `_resolve_hstore_field()` exist. They do not. The moved function bodies were:

```python
def _resolve_array_field() -> type[models.Field] | None:
    try:
        from django.contrib.postgres.fields import ArrayField
    except ImportError:
        return None
    return ArrayField


def _resolve_hstore_field() -> type[models.Field] | None:
    try:
        from django.contrib.postgres.fields import HStoreField
    except ImportError:
        return None
    return HStoreField
```

### Decision 5 — `HStoreField` wire shape

**Alternatives rejected, and why each lost.** The spec's four-bullet "Why reject `choices` rather than ignore" list, moved:

- Consistency with the `ArrayField` outer-`choices` rejection (Decision 2).
- Loud over silent: ambiguous configuration surfaces at type-creation time instead of producing a schema that emits values the consumer did not expect.
- Django allows declaring `choices` on `HStoreField` syntactically (for admin / form widget purposes), but the constraint is form-only and not enforced at the column level. The rejection forces the consumer to model the constrained shape explicitly.

The third bullet is the only one carrying information a reader cannot derive from Decision 2, so the reconciled spec keeps a one-sentence version of it and this file keeps the rest.

**Also rejected:** a dedicated `HStore` scalar (rejected as scope — `HStoreField` and `JSONField` therefore share `JSON` and are indistinguishable at the GraphQL type level, an accepted cost); expressing HStore as `dict[str, str | None]` (impossible — Strawberry rejects the annotation).

**Changes this decision has undergone:** rev 8 (H1) added the outer-`choices` rejection and its pseudocode, which rev 7 and earlier did not have; rev 10 (L1) propagated the policy into Goals, Non-goals, and the API table. `DONE-029-0.0.9` and commit `62ae8404` changed this branch the same way they changed Decision 2's.

### Decision 6 — `BigInt` public-export status and registration contract

This decision changed more than any other, and the whole of its deliberation is moved.

**Rev 7 (H1) rewrote it once already.** The pre-rev-7 claim — that "the public `BigInt` symbol stays the same, only the internal definition mechanism changes" — was judged too strong and retracted: under `scalar_map`, `BigInt` may need to become a bare `NewType`, and consumers using it directly would have to merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`. Rev 7's replacement was the honest two-state version:

> - *In `0.0.6`*: `BigInt` is a Strawberry `ScalarWrapper` (the return value of `strawberry.scalar(NewType(...))`). It works as a direct field annotation without any schema config.
> - *In the warning-free follow-up*: `BigInt` may become a bare `NewType` (or stay as a `ScalarWrapper` exported alongside a config helper). Consumers using `BigInt` directly will need to merge a package-provided `StrawberryConfig(scalar_map={...})` into their `strawberry.Schema(...)` call. A bare `NewType("BigInt", int)` annotation without `scalar_map` fails Strawberry schema construction with `Unexpected type '...BigInt'` — verified by probe.

**The follow-up shipped, and the second branch is what happened.** `DONE-025-0.0.7` made `BigInt` a bare `NewType`. The `0.0.6` bullet above is now historical and the "may become" hedge is settled. The reconciled spec states the single current contract directly, and the `Unexpected type '...BigInt'` failure — a live consequence a reader needs — was promoted from a probe result in the follow-up branch into a normative sentence in the spec.

**The "Recommended starting point" paragraph is moved in full.** It was a spec pre-designing a card that had not been written, hedged three ways ("this spec author has thought through alternatives and pinned a vetted direction, but the follow-up author may react to new information"). Its recommendation — a factory function `strawberry_config(extra_scalar_map=None) -> StrawberryConfig`, composable with consumer extras, forward-extensible for future package scalars, migrating consumers in a single added `config=` argument — is precisely what shipped, down to the parameter name. Its one explicit exclusion also held: `extra_extensions=` was deliberately kept out of the signature because Strawberry extensions are passed to `strawberry.Schema(..., extensions=[...])`, not into `StrawberryConfig`, and the shipped factory has no such parameter.

**Rev 9 (M3)** softened "Committed architectural direction" to "Recommended starting point" so the follow-up author could react to new information. In the event the follow-up author did not need to.

**Claims this decision may no longer make:** that `BigInt` is a `ScalarWrapper`; that it works as a direct field annotation without schema config; that the migration is an open follow-up rather than a shipped one; that the follow-up card's body is drafted inline in this spec.

**Card-name residue.** The follow-up was referred to three different ways inside one document — `WIP-ALPHA-020-0.0.7`, `TODO-ALPHA-045`, and `DONE-025-0.0.7`. The reconciliation settled on `DONE-025-0.0.7`, the card that actually shipped, on the evidence of `KANBAN.md`'s live card and [`spec-025-scalar_map_helper-0_0_7.md`][spec-025]'s own `Predecessors:` line. The other two spellings are pre-renumber artifacts.

### Decision 7 — test strategy

**Alternatives rejected:**

- **`importlib.reload`-based deprecation testing.** Rejected in rev 8 (H2) after the reviewer verified it cannot fail: `importlib.reload(django_strawberry_framework)` does not reload submodules, so `scalars.py`'s definition line never re-executes and the test observes zero warnings whether or not the suppression is present. Subprocess isolation replaced it. This is the one rev-7-through-10 mechanism that survives verbatim at `HEAD`, and the reasoning stayed in the spec because a future maintainer "simplifying" the subprocess away would reintroduce a test that cannot fail.
- **A shared `tests/types/conftest.py` for the autouse `registry.clear()` fixture.** Rev 8 (H3) established that no such file exists; each test file declares its own `_isolate_registry`. The spec was corrected to describe reality rather than to propose the conftest.
- **Session-scoped synthetic-model fixtures** for this card's tests. Both precedents were documented (in-function declaration and session-scoped unique-`app_label`); the in-function pattern was chosen because every fake-field test pairs a `monkeypatch.setattr` with a `DjangoType` declaration in one function, keeping the swap adjacent to the conversion trigger. Unique-`app_label`-per-test was named as the fallback if pytest-xdist warnings surfaced.
- **`isinstance(BigInt, strawberry.types.scalar.ScalarWrapper)`** in the import smoke test. Dropped in rev 9 because `ScalarWrapper` is an undocumented internal Strawberry path. Correct for a reason rev 9 could not have known: the assertion would have failed after `DONE-025-0.0.7`.

**The `managed = False` rationale was itself wrong once.** Rev 10 (L2) corrected it: bare `models.Field` subclasses do not trigger `Model.check()` warnings regardless of `managed`, so the flag's real purpose is avoiding migration implications and reminding implementers to instantiate test models directly rather than via `objects.create()`. The corrected version is in the spec.

**Changes this decision has undergone since shipping.** The four `_resolve_*_field` helper-resolver test bodies were removed from the spec by this pass because the helpers they test do not exist. Their `sys.modules`-manipulation technique survives at the shared helper's own tests, where `monkeypatch.setitem(sys.modules, name, None)` is still how the unimportable branch is forced.

**The nine promoted tests.** Nine schema-execution tests the spec names in Slices 1 and 2 were moved to the live `/graphql/` tier under different names, per the repository's live-first rule ([`AGENTS.md`][agents]: any line reachable via a real GraphQL query against fakeshop must be covered in `examples/fakeshop/test_query/`). The per-test mapping, re-derived rather than accepted:

| Spec-named test (absent at `HEAD`) | Live-tier test pinning the same contract |
|---|---|
| `test_big_integer_field_maps_to_bigint_in_schema` | `test_scalars_api.py::test_scalar_specimen_introspects_bigint_scalar_for_both_fields` — `signedBig` introspects `NON_NULL(BigInt)` |
| `test_big_integer_field_nullable_in_schema` | same test — `NullableScalarSpecimenType.signedBig` introspects bare `SCALAR BigInt` |
| `test_positive_big_integer_field_maps_to_bigint_in_schema` | same test — `unsignedBig` (a `PositiveBigIntegerField`) in both shapes |
| `test_bigint_serializes_query_result_as_string_via_schema_execution` | `::test_scalar_specimen_every_field_wire_format_over_http` — `row["signedBig"] == "9223372036854775000"`, a value past `2**53 - 1` so only decimal-string serialization can survive the JSON round-trip |
| `test_bigint_parses_string_argument_via_schema_execution` | `::test_scalar_specimen_bigint_input_decimal_string_argument_over_http` |
| `test_bigint_parses_int_argument_via_schema_execution` | `::test_scalar_specimen_bigint_input_int_literal_argument_over_http` |
| `test_json_field_maps_to_json_scalar_in_schema` | `::test_scalar_specimen_introspects_json_scalar_in_both_shapes` — `payload` introspects `NON_NULL(JSON)` |
| `test_json_field_nullable_in_schema` | same test — `NullableScalarSpecimenType.payload` introspects bare `SCALAR JSON` |
| `test_json_field_round_trips_dict_via_schema_execution` | `::test_scalar_specimen_every_field_wire_format_over_http` — `row["payload"] == _JSON_PAYLOAD`, a mixed-primitive dict whose module-level comment names this migration explicitly |

Three of the live tests carry the migration in their own docstrings ("Migrated from these tests in `tests/types/test_converters.py`: …"), and the file's `_JSON_PAYLOAD` comment names `test_json_field_round_trips_dict_via_schema_execution` by name. The remaining spec-named converter tests — `test_big_auto_field_still_maps_to_int`, `test_bigint_in_input_position_with_null_via_schema_execution`, the two reject-argument tests, and the resolver-returning-`bool` test — all still exist at the package tier under their own names, as do all thirty-one `tests/test_scalars.py` names and all fifteen sentinel-branch names.

### Decision 8 — `SCALAR_MAP` value type widening

No deliberation to move. Introduced in rev 2, unchanged, present at `HEAD`.

### `## Slice checklist` — Slice 5 and Slice 6

**Moved from Slice 5.** The "controlled inconsistency" framing: the quintet covers programmatically-checked version sites, the two consumer-facing version strings land in Slice 6, and "the result is a controlled inconsistency between Slice 5 landing and Slice 6 closing: PyPI metadata reads `0.0.6` but `README.md` / `docs/README.md` still say `0.0.5`." The *rule* (the PyPI publish gate) stayed; the narration of the inconsistency moved.

**Moved from Slice 6 — the NNN renumber, rejected twice.** An earlier draft offered renumbering `TODO-ALPHA-020` through `044` to `021` through `045`, so the new follow-up card would sit adjacent to its version cluster. Rev 9 (M1) removed the option entirely: a multi-file cascading rename across 5+ files and 50+ string sites, with stale-link risk for any external doc, PR, or CHANGELOG citing a card NNN. The replacement rule — append at the next available NNN, because `KANBAN.md` groups by version rather than by NNN — is in the spec; the rejected alternative is here.

**Moved from Slice 6 — two verbatim card bodies.** Slice 6 reproduced the full `DONE-017-0.0.6` KANBAN body and the full follow-up card body inline, plus an archive-time instruction to strip the second one and replace it with a "See `KANBAN.md`" pointer. All of it is moved. `KANBAN.md` is generated from the fakeshop kanban database, so a verbatim copy in the spec drifts against the live card by construction — the very hazard rev 9 (M2) identified and tried to patch by stripping only one of the two bodies. The reconciled spec reproduces neither and points at `KANBAN.md` instead.

**The self-contradicting move instruction.** Slice 6 read `move DONE-017-0.0.6 -> DONE-017-0.0.6` — a card-renumber residue where both sides of a status-flip instruction were rewritten to the post-renumber name. Deleted, not moved: it instructs nothing.

**Claims Slice 6 may no longer make:** that the spec is yet to be archived (it sits at `docs/SPECS/spec-017-deferred_scalars-0_0_6.md`, its terms CSV at `docs/SPECS/appx/`); that a "DONE-013" body and a "TODO-045" body are the things being dropped in; that `docs/GLOSSARY.md` and `KANBAN.md` are hand-edited files (both are rendered from `examples/fakeshop/db.sqlite3`).

**A `CHANGELOG.md` entry the follow-up removed.** Slice 6 specified a `Notes` entry documenting the suppressed deprecation. `DONE-025-0.0.7` Slice 5 deleted that line from the `[0.0.6]` section, on the reasoning that a forward-looking "tracked as a follow-up" pointer has served its purpose once the follow-up ships. The reconciled Slice 6 no longer specifies it.

### `## Risks and open questions`

**Moved.** The whole section, thirteen bullets. Every one is either settled or superseded:

- **The suppression risk and its thread-safety caveat.** The caveat was real and carefully argued — `warnings.catch_warnings()` is not thread-safe, but the package's use was single-threaded module-load protected by the CPython import lock, with a note that a future re-architecture importing `scalars.py` from a worker thread would need to revisit. Fully moot: there is no `catch_warnings()` in `scalars.py`.
- **The `scalar_map` follow-up as a real public-API migration.** Settled by `DONE-025-0.0.7`; see the Decision 6 entry.
- **`PositiveBigIntegerField` wire-format change.** Accepted as breaking-but-alpha, documented in `CHANGELOG.md`. Shipped.
- **`BigAutoField` deferred with "no current-day recourse".** Superseded: the sibling card `DONE-019-0.0.6` shipped consumer annotation overrides in the same release, so the recourse existed from `0.0.6` onward. `KANBAN.md`'s card body was updated to say so; **four** places in this spec were not - the Risks bullet, `## Non-goals`, Decision 1's "Target Django fields" list, and `## Edge cases and constraints`. All four are deleted rather than moved; the full population and the pass that closed each is under Decision 1 below.
- **`HStoreField` and `JSONField` share `JSON`.** Still true, still accepted; a dedicated `HStore` scalar remains a possible future card. Recorded in the spec's Non-goals rather than as a risk.
- **`BigInt` name collision with Apollo Federation.** A post-`1.0.0` concern; unchanged.
- **`BigInt` arbitrary precision.** Canonically framed in Decision 1; the risk bullet was a pointer.
- **`ArrayField` of `DecimalField` untested.** Still true; relies on inheritance from existing `DecimalField` tests plus the recursion test.
- **Multi-dimensional `ArrayField`.** Rejected; liftable in a future card.
- **`T | None` for `NewType` / `ScalarWrapper` on Python 3.10+.** Verified at the time and gated by CI ever since.
- **`sys.modules` manipulation in helper-resolver tests.** The tests moved to `tests/utils/test_imports.py`; the technique and its low risk are unchanged.
- **Strict serializer tradeoffs.** A pointer to Decision 1.
- **`tests/types/test_converters.py` size growth.** Predicted ~420 to ~1100 lines, with a follow-up threshold at ~1500. The file is past that threshold at `HEAD`, but the live-first migration has been removing tests from it rather than adding, so the predicted concern-specific split (`tests/types/test_converters_scalars.py`) was never needed.

## Reconciliation record — what the spec now says, and why

The move and the reconciliation ran in one pass, so this file carries both records.

**Strategy.** State the contract that holds at `HEAD`, with no amendment block, no retraction paragraph, and no "as of revision N" hedge — the spec must read as though it had been right from the start ([`docs/builder/BUILD.md`][build] `## Spec rationale extraction`). Where a later card superseded a mechanism, the spec describes the *current* mechanism and this file records the old one. Where a later card superseded a *goal*, the goal is restated in the terms that now hold.

**Section by section:**

- **Header.** `Status:` flipped from `draft (revision 10, …)` to `shipped in 0.0.6`; a pointer to this file added.
- **`Revision history`, `## Current state`, `## Risks and open questions`.** Removed entirely; entries above.
- **`## Key glossary references`.** The `Scalar field override semantics` bullet's `planned for 0.0.6 (WIP-ALPHA-015)` corrected to the sibling card `DONE-019-0.0.6`, which shipped.
- **`## Slice checklist` Slice 1.** The `warnings.catch_warnings()` instruction replaced by the warning-free-import requirement. The "Deprecation suppression (B1 coverage)" sub-heading retitled "Warning-free import (B1 coverage)". The six `BigInt` schema-execution boxes and the three `JSONField` boxes in Slice 2 repointed at their live-tier equivalents, path-qualified so a reader can find them; the four package-tier survivors path-qualified too, so the two tiers are visually distinguishable.
- **Slices 3 and 4.** `_resolve_array_field()` / `_resolve_hstore_field()` replaced by the shared soft-import owner; the four helper-resolver test boxes replaced by a pointer to `tests/utils/test_imports.py` naming it as the owner, so a future reader does not "restore" the deleted duplication.
- **Slice 5.** Deliberation trimmed; the version sites and the publish gate kept.
- **Slice 6.** Rewritten. Both verbatim card bodies removed, the self-contradicting move instruction removed, the archive-time stripping step removed, the generated-doc procedure (`edit the database, then regenerate`) stated for `docs/GLOSSARY.md` and `KANBAN.md`, the follow-up card named as `DONE-025-0.0.7`, the version bumps de-pinned from literal `0.0.5` to "the release this card ships in", and the archive step extended to name the `appx/` companions. **This cycle owed no move: the spec and its terms CSV were already at their archived locations, and nothing was re-archived.**
- **`## Problem statement` constraint 4.** Rewritten from "the deprecation is suppressed" to "the package must define `BigInt` on the non-deprecated path", which is both the current mechanism and the original goal.
- **`## Goals`, `## Non-goals`, `## User-facing API`.** The suppression bullet, the `No StrawberryConfig.scalar_map integration` non-goal, and the API table's revision-7 footnote all restated against the shipped registration contract.
- **Decisions 1, 2, 4, 5, 6, 7.** As above.
- **`## Test plan`.** The two-file preamble expanded to three, naming the live tier and stating why `ArrayField` / `HStoreField` stay at the package tier (postgres-only, unreachable from a SQLite-backed example). Category 12 repointed at the shared helper's tests; category 17 retitled.
- **`## Definition of done`.** The archive item extended to name the companions; the deprecation-suppression item retitled.
- **Link scaffold.** Two definitions added under `<!-- docs/SPECS/ -->` (`[spec-017-rationale]`, `[spec-025]`). All in-page anchors re-verified to resolve against a heading; `check_spec_glossary.py` re-run to exit 0.

### What this cycle deliberately did not fix

- **The `[spec-013]` ref-id cluster in [`spec-025-scalar_map_helper-0_0_7.md`][spec-025]** — five links whose *label* is a pre-renumber artifact although the definition resolves correctly. `KANBAN.md` already records the whole multi-surface cluster as carded onto `TODO-ALPHA-051-0.0.15` / `TODO-ALPHA-052-0.1.0`. Correcting one surface would leave the cluster divergently rather than uniformly wrong.
- **Standing-doc staleness** (`KANBAN.md`'s `DONE-017-0.0.6` body still claiming the deprecation is "suppressed at the definition site"; `docs/GLOSSARY.md`; `CHANGELOG.md`; `docs/README.md`; `TODAY.md`). These belong to this cycle's R3 round and are enumerated in the R1 artifact for it.
- **Any code change.** The audit found no gap and no defect, so no R2 round was opened.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->
[glossary-strawberry-config]: ../../GLOSSARY.md#strawberry_config
[glossary-upload-scalar]: ../../GLOSSARY.md#upload-scalar

<!-- docs/SPECS/ -->
[spec-015-rationale]: spec-015-relay_interfaces-0_0_5-rationale.md
[spec-016-rationale]: spec-016-fieldmeta_consolidation-0_0_6-rationale.md
[spec-017]: ../spec-017-deferred_scalars-0_0_6.md
[spec-025]: ../spec-025-scalar_map_helper-0_0_7.md
[spec-029]: ../spec-029-consumer_dx_cleanup-0_0_9.md
[spec-041]: ../spec-041-channels_router-0_0_14.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
