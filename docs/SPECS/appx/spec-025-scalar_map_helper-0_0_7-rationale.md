# Rationale: spec-025 — Warning-free scalar registration via `StrawberryConfig.scalar_map` (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-025-scalar_map_helper-0_0_7.md`][spec-025]. The spec is the contract and states only what it requires; everything that explains **how it got there** lives here: the revision history the spec carried inline, the justification and rejected alternatives behind each of the nine Decisions, the `Explicitly do not borrow` rejections, the contingency reasoning the risks section carried, and every claim a Decision once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass, run late — as a residual-completion cycle rather than at the card's own pre-flight, because the original `025` cycle never performed step 7. It was produced by Slice 1 of [`docs/builder/build-025-scalar_map_helper-0_0_7.md`][build-025]. Slice 2 of that plan reconciled the spec against `HEAD`; the thirteen divergences it acted on are recorded below under [Post-ship divergence record](#post-ship-divergence-record-d1-d14) — each entry written before the rewrite ran, so the rewrite can be checked against a statement of what was wrong, and each closed with the edit that discharged it. Slice 3 added a fourteenth entry to that record, [D14](#d14--fakeshop-gained-a-second-schema-construction-site), found after the final gate and outside anything Slice 2 acted on; the record therefore holds fourteen entries while Slice 2's own figure stays thirteen.

## Provenance of this record

**This pass performed a MOVE, not a reconstruction.** Every block under a `### Justification (moved from the spec)` or `### Alternatives considered (and rejected)` heading below, the whole of [Revision history](#revision-history), the three [Explicitly do not borrow](#borrowing-posture--explicitly-do-not-borrow) bullets, and the quoted clauses under [Deliberation moved from the risks section](#deliberation-moved-from-the-risks-section) were **cut** from the spec by this pass and are byte-for-byte as the spec carried them. One script extracted each block by line span, wrote it here, and deleted it there in the same run, so a copy-instead-of-cut is structurally impossible rather than merely checked for afterwards.

Two classes of text here are **new material**, and a reader who cannot tell them apart cannot trust either:

- the per-Decision `### Changes this Decision underwent` and `### Claims this Decision may no longer make` records. The original cycle never wrote a change record because it never ran this pass; these were derived by reading the shipped source and the divergence catalog, not recovered from the spec.
- the whole [Post-ship divergence record](#post-ship-divergence-record-d1-d14) and [Facts re-verified as still true at HEAD](#facts-re-verified-as-still-true-at-head).

Two mechanical alterations were applied to the moved bytes, and nothing else:

- **Re-relativization.** The spec sits at `docs/SPECS/`, this file one level deeper at `docs/SPECS/appx/`, so an inline `](../../CHANGELOG.md)` in moved text became `](../../../CHANGELOG.md)`. The move left the moved text's `.venv/lib/python3.10/...` citations exactly as written even though they were already dead at `HEAD`; the reconciliation slice re-pointed them at `python3.14` in the same sweep that fixed the spec's, so no dead path survives here — see [D12](#d12--every-venv-citation-points-at-python310-and-the-strawberry-floor-is-restated-stale). Nothing else about the moved bytes changed.
- **Two in-page anchors re-pointed at the spec.** Moved text citing `](#error-shapes)` and `](#risks-and-open-questions)` would have dangled here (this file has no such heading), so both became reference links into the spec. Moved `](#decision-N--…)` anchors were left in place: this file's Decision headings carry the spec's titles verbatim, so they resolve to the matching entry, which in turn names the spec text on its first line.

**One justification bullet did NOT move.** Decision 7's `**Defense-in-depth note (intentional duplication with `tests/types/test_converters.py`).**` stayed in the spec, re-homed as Decision 7 body prose, under the [`docs/builder/BUILD.md`][build] carve-out for implementation-relevant rationale: it is the reason a future DRY pass may not delete two integration tests, so it changes how the code is maintained rather than merely explaining how the Decision was reached. It is deliberately absent from this file — the two files do not both carry it.

What the spec carried immediately before the cut, measured at this working tree:

| Population | Measured | Instrument |
|---|---|---|
| spec bytes before the pass | 135,777 | `wc -c` |
| `Revision history` entries, inline | 1 | `grep -cE '^\- \*\*Revision [0-9]+\*\*'` |
| `Justification:` blocks at line start | 9 | `grep -c '^Justification:'` |
| `Justification`-prefixed clauses **anywhere** | 9 | `grep -oE 'Justification[a-z ]*:' \| wc -l` |
| justification bullets under those 9 blocks | 38 (37 moved, 1 retained) | counted per block from the extractor's line spans: `[3, 8, 3, 4, 4, 3, 5, 4, 4]` |
| `Alternatives considered (and rejected):` blocks | 9 | `grep -c '^Alternatives considered (and rejected):'` |
| rejected-alternative bullets under those 9 blocks | 28 | counted per block from the extractor's line spans |
| `### Explicitly do not borrow` rejection bullets | 3 | the section's own `- ` lines |
| `## Risks and open questions` bullets | 8 | the section's own `- **` lines |
| `Preferred answer:` clauses | 8 | `grep -o 'Preferred answer:' \| wc -l` |
| `Fallback:` clauses | 8 | `grep -o 'Fallback:' \| wc -l` |

The clause-level counts are the load-bearing ones. A `Justification`-prefixed clause **anywhere** (9) equalling the line-start block count (9) is what proves no inline justification survived outside the nine blocks; a block count alone cannot see one. And `grep -c` counts *lines*, not occurrences, so every population that can appear more than once on a line was taken with `grep -o | wc -l`.

## Revision history

Moved from the spec head, where it was introduced by the line "Revision history (kept inline so the spec is self-contained)". `025` shipped on its first revision, so this is the whole of it — there is no multi-revision chronology behind any Decision, which is why the per-Decision change records below are all post-ship.

- **Revision 1** — initial draft. Pins the canonical spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)), the helper API shape and module location ([Decision 2](#decision-2--helper-api-shape-and-module-location)), the `BigInt` redefinition as a bare `NewType` with the `ScalarDefinition` produced by `strawberry.scalar(name=..., serialize=..., parse_value=...)` (the no-warning overload at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar]) ([Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition)), the conflict-resolution policy for `extra_scalar_map` collisions ([Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions)), the hard-break-in-alpha migration posture ([Decision 5](#decision-5--migration-posture-hard-break-in-alpha)), the suppression-removal contract ([Decision 6](#decision-6--remove-the-warningscatch_warnings-suppression-block)), the test placement strategy ([Decision 7](#decision-7--test-placement-and-shape)), the version posture for a post-cut card ([Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut)), and the example-app migration scope ([Decision 9](#decision-9--example-app-migration-scope)). Out of scope: composing extensions through this helper (the card body already calls this out — `extensions=` belongs on `strawberry.Schema(...)`, not `StrawberryConfig`; a future "schema-construction bundle" helper is a separate card if real demand surfaces); auto-discovery of the package config (a Django `settings`-backed default `STRAWBERRY_CONFIG_FACTORY = "django_strawberry_framework.scalars.strawberry_config"` shortcut) — deferred until the discovery story is needed; promoting `Upload` (the next package-defined scalar, planned for `0.0.11` per [`docs/GLOSSARY.md#upload-scalar`][glossary-upload-scalar]) — that card consumes this card's helper without modifying it.

## Decision 1 — Spec filename and canonical naming

Spec text: [Decision 1][spec-025-d1]. Contract that stays: the spec carries the structured stem `spec-025-scalar_map_helper-0_0_7`, and a reference points at whichever path the file actually has at the time the reference is written.

### Justification (moved from the spec)

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 and proven by every recent spec ([`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-018], [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019], [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020], [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021], [`docs/SPECS/spec-022-export_schema-0_0_7.md`][spec-022], [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023]) bakes the card's NNN and target patch into the filename. The card body's `docs/spec-scalar_map_helper.md` predates that convention and would land an unnumbered spec next to a numbered cohort, breaking the alphabetical archive ordering at `docs/SPECS/`.
- The Slice 5 [`KANBAN.md`][kanban] update overwrites the stale `docs/spec-scalar_map_helper.md` reference in the card body to point at the canonical name, so the cross-reference resolves after archival (per [Step 8 of NEXT.md][next-step-8]).
- This Decision is enforcement, not innovation: the convention is already pinned in [`docs/SPECS/NEXT.md`][next] Step 6 and observed by every spec from 014 forward.

### Alternatives considered (and rejected)

- **Honor the card body verbatim with `docs/spec-scalar_map_helper.md`.** Rejected: diverges from the structured naming convention; forces a Step-8 archive rename anyway; would not match the [`KANBAN.md`][kanban] sibling cards' filenames.
- **Use a longer topic slug like `strawberry_config_factory`.** Rejected: longer than necessary; `scalar_map_helper` already names the architectural intent and matches the card body's recommended filename minus the `docs/spec-` prefix.

### Changes this Decision underwent

- **No pre-ship change.** `025` shipped on Revision 1, so this Decision reached the shipped spec in the form it was drafted in.
- **Post-ship, the path lifecycle resolved itself.** The archive pass has run: the spec is at `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` and its terms CSV at [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms], with this file beside it. The Decision's rule ("whichever path the file actually has") is what makes that a resolution rather than a contradiction.

### Claims this Decision may no longer make

- That the spec is the *active* in-flight document at `docs/spec-025-scalar_map_helper-0_0_7.md`. The archive has happened; that path does not exist.
- That a maintainer re-tag could move the file to `docs/spec-020-scalar_map_helper-0_0_8.md` under a `WIP-ALPHA-020-0.0.8` card. The 2026-07-30 board renumber gave `020` to `DjangoListField`; this card is permanently `DONE-025-0.0.7`. See [D11](#d11--the-re-tag-hypothetical-is-dead-not-stale).

## Decision 2 — Helper API shape and module location

Spec text: [Decision 2][spec-025-d2]. Contract that stays: `strawberry_config(*, extra_scalar_map=None, **config_kwargs) -> StrawberryConfig`, a factory (never a shared constant, never a `Schema` wrapper), living in [`django_strawberry_framework/scalars.py`][scalars] and re-exported from the package root; `scalar_map=` is rejected.

### Justification (moved from the spec)

- **Factory over static constant.** A factory function returns a fresh `StrawberryConfig` per call, so two schemas (e.g., the main app schema plus a debug-tools admin schema) get independent `StrawberryConfig` instances and one's mutations cannot leak to the other. A static `STRAWBERRY_CONFIG: StrawberryConfig` module-level constant would share mutable state across every call site.
- **Factory over class wrapper.** Wrapping `strawberry.Schema(...)` (e.g., `dst.Schema(query=..., ...)`) shadows the upstream symbol and hides composition. The factory returns a `StrawberryConfig` and the consumer composes it into their own `strawberry.Schema(query=..., config=strawberry_config(), extensions=[...])` call — same posture as `DjangoOptimizerExtension()` being composed via `extensions=[...]`.
- **`**config_kwargs` passthrough for non-scalar `StrawberryConfig` fields.** Strawberry's `StrawberryConfig` has many fields beyond `scalar_map` ([`auto_camel_case`, `name_converter`, `default_resolver`, `relay_max_results`, `relay_use_legacy_global_id`, `disable_field_suggestions`, `info_class`, `enable_experimental_incremental_execution`, `scalar_map`, `batching_config`][config]); the only one this card has an opinion on is `scalar_map`. The helper forwards every other kwarg verbatim, so consumers who want to set `auto_camel_case=False` or `relay_max_results=200` write `strawberry_config(auto_camel_case=False, relay_max_results=200)` and get one `StrawberryConfig` carrying both the package scalars and the consumer's tuning. The helper does NOT enumerate the supported upstream kwargs because the supported set is owned by Strawberry and would drift with Strawberry releases; unknown kwargs surface as the upstream's own `TypeError`.
- **`scalar_map=` rejected as a kwarg.** Passing `scalar_map=` directly to `strawberry_config(...)` raises `ValueError("strawberry_config() owns scalar_map; pass consumer scalars with extra_scalar_map=...")` per [Error shapes][spec-025-error-shapes]. Letting it through would bypass the [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) conflict-resolution policy that the helper exists to centralize.
- **Keyword-only `extra_scalar_map`.** The leading `*,` in the signature forbids the positional form `strawberry_config({...})`; consumers must spell `extra_scalar_map=...` explicitly. This pairs with the `**config_kwargs` passthrough: anything in the call that isn't `extra_scalar_map` is treated as a `StrawberryConfig` kwarg, so positional invocation would be ambiguous between "scalar map" and "first positional StrawberryConfig argument" if both shapes were permitted. The keyword-only constraint resolves that ambiguity by construction.
- **`extra_extensions=` deliberately omitted.** Strawberry extensions go to `strawberry.Schema(..., extensions=[...])`, not into `StrawberryConfig`. The card body calls this out explicitly. If a future card reveals real demand for extension-bundling, it ships as a separate helper (e.g., `schema_kwargs(...)` returning a dict of `{"config": ..., "extensions": [...]}`) rather than overloading this one.
- **Module location: [`scalars.py`][scalars] (NOT a new `config.py`).** Cohesion: everything BigInt-related lives in one module. The factory's body is small (~15 lines), and the package's existing flat-module layout already mirrors `strawberry-django`'s shape (`apps.py`, `arguments.py`, `descriptors.py`, etc.). A new module would also be ambiguously named relative to the existing `conf.py` (the settings-reader for `DJANGO_STRAWBERRY_FRAMEWORK`); two `conf.py` / `config.py` files would be a maintenance hazard. When `Upload` lands (`DONE-037-0.0.11`), its `ScalarDefinition` joins the same module's `_PACKAGE_SCALAR_MAP` dict — no additional file proliferation.
- **Type signature.** `Mapping[object, ScalarDefinition] | None` on `extra_scalar_map` matches Strawberry's own `StrawberryConfig.scalar_map: Mapping[object, ScalarDefinition]` shape at [`.venv/lib/python3.14/site-packages/strawberry/schema/config.py #"scalar_map: Mapping[object, ScalarDefinition]"`][config]; `object` keeps the key type as broad as Strawberry's contract; `| None` lets callers omit the parameter entirely. `**config_kwargs: Any` keeps the passthrough type-broad on purpose — the helper's signature does not duplicate Strawberry's per-kwarg type contracts.

### Alternatives considered (and rejected)

- **`django_strawberry_framework/config.py` (new module).** Rejected: ambiguity with the existing [`conf.py`][conf] (the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader); two modules differing only in vowels invite consumer error and reader confusion.
- **`django_strawberry_framework/__init__.py` (top-level only — no separate module).** Rejected: bloats the entry-point with implementation. The existing `__init__.py` is the public-surface manifest (re-exports and `__all__`); the helper's body belongs next to the scalar it composes.
- **`django_strawberry_framework/schema.py` (new module).** Rejected: name collides conceptually with `strawberry.Schema`; would suggest the helper does more than build a `StrawberryConfig`.
- **`strawberry_config(extra_scalar_map=None)` only — no `**config_kwargs`.** Rejected: leaves consumers who want `auto_camel_case=False` or `relay_max_results=200` with no supported composition path. The earlier draft of this spec claimed they could "construct their own `StrawberryConfig(...)` and merge the package's `scalar_map` via `extra_scalar_map=`", but that is not a real API path — `extra_scalar_map=` is on the helper, not on the upstream constructor, and `_PACKAGE_SCALAR_MAP` is private. The `**config_kwargs` passthrough fills that gap with one supported call shape.
- **Promote `_PACKAGE_SCALAR_MAP` to a public `PACKAGE_SCALAR_MAP` re-export.** Rejected: creates two parallel public composition paths (`strawberry_config()` AND `PACKAGE_SCALAR_MAP` spread into upstream `StrawberryConfig(...)`); pushes the conflict-resolution policy from [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) onto consumers; doubles the public-export surface for an audience the `**config_kwargs` passthrough already serves.
- **`strawberry_config(*, scalar_map=None)` (keyword-only, no `extra_` prefix).** Rejected: a bare `scalar_map=` parameter implies "this REPLACES the package's defaults"; `extra_scalar_map=` makes the merge-not-replace intent explicit. The same kwarg name is what the helper rejects when it lands inside `**config_kwargs`, so reusing it on the front-door parameter would be doubly confusing.
- **`strawberry_config(*, replace_scalar_map=None, extra_scalar_map=None)` (two parameters).** Rejected: introduces a "replace mode" the package has no business supporting — replacing `BigInt`'s registration would silently break the `BigIntegerField → BigInt` converter table.

### Changes this Decision underwent

- **No pre-ship change.** The signature shipped exactly as pinned, verified byte-for-byte against the spec's code block by the cycle's pre-dispatch pass.
- **Post-ship, the module gained a public `__all__`** — `["BigInt", "Upload", "UploadDefinition", "strawberry_config"]` — which the Decision's pinned import surface did not contemplate. See [D2](#d2--scalarspy-now-declares-a-module-__all__).
- **Post-ship, the module gained the `Upload` re-export**, and it arrived by a different mechanism than this Decision predicted. See [D3](#d3--the-upload-forward-compatibility-prediction-was-wrong-in-mechanism).

### Claims this Decision may no longer make

- That when `Upload` lands, "its `ScalarDefinition` joins the same module's `_PACKAGE_SCALAR_MAP` dict" (moved above, in the module-location bullet). It did not, and could not: `Upload` is Strawberry's own `NewType("Upload", bytes)`, already carried by `DEFAULT_SCALAR_REGISTRY`. The bullet's *conclusion* — no file proliferation, everything scalar-shaped stays in one module — held. Its *mechanism* was wrong. See [D3](#d3--the-upload-forward-compatibility-prediction-was-wrong-in-mechanism).
- That the helper's body is "~15 lines". It is roughly twice that at `HEAD`, after the materialization guard and the collision-label helper. The conclusion the figure supported (a body this small does not earn its own module) is untouched.

## Decision 3 — `BigInt` redefinition as bare `NewType` + `ScalarDefinition`

Spec text: [Decision 3][spec-025-d3]. Contract that stays: `BigInt = NewType("BigInt", int)` bare, with the `ScalarDefinition` built through the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload, and the decimal-string wire format unchanged.

### Justification (moved from the spec)

- The `strawberry.scalar(cls=None, name=...)` overload returns a `ScalarDefinition` directly and does NOT emit the `DeprecationWarning`. Verified at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar]: the branch is `return ScalarDefinition(name=name, description=..., specified_by_url=..., serialize=serialize, parse_literal=parse_literal, parse_value=parse_value, directives=..., origin=None, ...)`. The deprecation-emitting `wrap()` body at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"def wrap(cls: _T) -> ScalarWrapper"`][scalar] is the `cls is not None` path.
- The bare `NewType("BigInt", int)` keeps `BigInt` usable as a direct Python annotation — `id: BigInt` and `def f(x: BigInt) -> BigInt: ...` work as type hints because `NewType` is a transparent identity at runtime. Strawberry resolves the `NewType` to the registered `ScalarDefinition` via `StrawberryConfig.scalar_map` at schema-construction time.
- The wire format, parser, and serializer logic are preserved verbatim — `_parse_bigint` and `_serialize_bigint` are unchanged from `0.0.6`. The only change at the Python level is the structure that wraps them.

### Alternatives considered (and rejected)

- **`BigInt = strawberry.scalar(NewType("BigInt", int), name=..., ...)` plus an unconditional `warnings.filterwarnings("ignore", ...)` in `scalars.py`.** Rejected: re-suppression of the deprecation defeats the card's purpose.
- **Use Strawberry's `Annotated[int, strawberry.argument(...)]` shape.** Rejected: `argument(...)` annotates parameters, not types; doesn't match `BigInt`'s "type used in annotations" role.
- **Subclass `int` for `BigInt` and bind the scalar definition to the subclass.** Rejected: `int` subclasses are heavier than `NewType` (real Python class with `__instancecheck__` cost), and `bool` issues at parse time (`isinstance(value, BigIntSubclass)` and `isinstance(value, bool)` interact awkwardly because `bool` is an `int` subclass). The bare `NewType` is the lighter, more idiomatic shape.

### Changes this Decision underwent

- **No pre-ship change.**
- **Post-ship, both function bodies were hardened** against hostile `int` / `str` subclasses (`int.__int__`, `str.__str__`, `int.__str__`, `_safe_arg_repr` / `_safe_type_name` in messages, `# noqa: TRY004` on the bool raise). The **wire format** is identical; the bodies are not. See [D4](#d4--_parse_bigint-and-_serialize_bigint-are-no-longer-unchanged-from-006).
- **Post-ship, the pinned code block stopped describing the shipped function** at two points: the `extra_scalar_map` materialization (see [D5](#d5--the-spec-specified-a-fail-open-shape-not-merely-tolerated-one)) and the collision-message label (see [D6](#d6--the-repr-fallback-is-now-a-helper-and-it-is-tested)).

### Claims this Decision may no longer make

- That "`_parse_bigint` and `_serialize_bigint` are unchanged from `0.0.6`" (moved above, justification bullet 3). True at ship, false at `HEAD`.
- That the pinned code block is the current body of [`django_strawberry_framework/scalars.py`][scalars]. It is the *shipped* body, which is a different claim and the only one the block can still support.

## Decision 4 — Conflict resolution for `extra_scalar_map` collisions

Spec text: [Decision 4][spec-025-d4]. Contract that stays: a key already in `_PACKAGE_SCALAR_MAP` raises `ValueError` naming the colliding keys and the supported recourse. No silent override, no warn-and-override, no `allow_override=` flag.

### Justification (moved from the spec)

- The collision is a consumer-input mistake at helper-call time, not a `DjangoType`-creation or finalization-time error. `ValueError` is the standard library's "function received an unsuitable argument" exception; using `ConfigurationError` (the package's own type-creation / finalization error class) would be inconsistent with what that exception class signals.
- Silently overriding the package default would let a consumer accidentally re-register `BigInt` to a different `ScalarDefinition` (e.g., one that serializes as a JSON integer instead of a decimal string), breaking the `BigIntegerField → BigInt` wire-format contract that the [`docs/SPECS/spec-017-deferred_scalars-0_0_6.md`][spec-017] Decision 1 pins. Silent override is the worst-of-both: it does what the consumer typed but breaks the contract they didn't realize they were touching.
- Override-with-warning is the worst-of-both in a different way: the schema still builds with potentially-broken semantics, and the warning is easy to miss in CI / dev terminal output. Hard error catches the mistake at helper-call time, before schema construction even starts.
- The error message names the offending key(s) so the consumer can identify which mapping to drop, and explicitly states the supported recourse (use a different key — a custom `NewType` or class — for the consumer scalar that's currently colliding).

### Alternatives considered (and rejected)

- **Silent override.** Rejected: catches no mistakes; the consumer never knows they replaced a package default.
- **Override with `UserWarning`.** Rejected: easy to miss; the schema still ships with overridden semantics.
- **Two-flag API: `strawberry_config(extra_scalar_map=..., allow_override=False)` defaulting to hard error.** Rejected: adds a complication to support a use case (intentional override) that the [Decision 2](#decision-2--helper-api-shape-and-module-location) "no replace mode" boundary already excludes.

### Changes this Decision underwent

- **No pre-ship change.**
- **Post-ship, the way the message names a key was replaced.** `getattr(k, '__name__', repr(k))` became `_safe_scalar_map_key_label`, which swallows a raising `__name__` descriptor and rejects a non-`str` `__name__`. The message's *contract* — names the keys, states the recourse — is unchanged. See [D6](#d6--the-repr-fallback-is-now-a-helper-and-it-is-tested).
- **Post-ship, a second `ValueError` joined this one at the same boundary**, for an `extra_scalar_map` that cannot be materialized. It is a sibling of this Decision's error, not a replacement, and the spec's `## Error shapes` section does not list it. See [D5](#d5--the-spec-specified-a-fail-open-shape-not-merely-tolerated-one).

## Decision 5 — Migration posture: hard break in alpha

Spec text: [Decision 5][spec-025-d5]. Contract that stays: a hard break in alpha — no deprecation window, no re-registration shim, no `legacy_bigint()` compat helper — and the migration surface includes consumers who never name `BigInt`, because the converter table names it for them.

### Justification (moved from the spec)

- Matches the `PositiveBigIntegerField` precedent in `0.0.6` (per [`docs/SPECS/spec-017-deferred_scalars-0_0_6.md`][spec-017] Decision 1, which switched `PositiveBigIntegerField` from `int` to `BigInt` — a breaking wire-format change shipped as a single Changed entry in `[0.0.6]`). The package's alpha-quality status (per [`README.md`][readme-repo]: "single-maintainer, alpha-quality. Fine for internal tools and prototypes; not production") makes hard breaks the right default while consumers are early.
- Long deprecation windows are appropriate at `1.0.0`, not during alpha. The [`docs/GLOSSARY.md`][glossary] status legend already pins: "The `1.0.0` release is the API-freeze boundary; after `1.0.0` ships, strict semantic versioning applies to every entry below." Pre-`1.0.0`, the contract is "names are stable, semantics evolve."
- The consumer migration is one line: add `config=strawberry_config()` (with the import) to the `strawberry.Schema(...)` call. The CHANGELOG entry under Slice 5 carries the explicit before/after block.
- Surveying real `0.0.6` consumer adoption of `BigInt` before deciding the posture is the [`KANBAN.md`][kanban] card body's "if real consumer demand" branch — but the package is single-maintainer-alpha and there is no consumer survey to consult; the right default is to apply the precedent (`PositiveBigIntegerField` in `0.0.6`) verbatim.

### Alternatives considered (and rejected)

- **One-release `DeprecationWarning` from the package.** Rejected: would require keeping the old `strawberry.scalar(NewType, ...)` path alongside the new one for one release, doubling the surface and the test load; consumers who ignore `DeprecationWarning` get a louder break later anyway.
- **`BigInt` keeps the wrapped shape; introduce `strawberry_config()` as a no-op helper consumers can opt into early.** Rejected: ships the suppression block for another release and defers the architectural cleanup the card exists to do; misses the "stop carrying the architectural debt" point.
- **Provide a `legacy_bigint()` compat helper consumers can swap in.** Rejected: every "compat helper" added during alpha is one more thing to deprecate at `1.0.0`; the boundary is "alpha-quality means consumers update their schema-construction call when the package updates."

### Changes this Decision underwent

- **No pre-ship change.**
- **No post-ship change.** No shim, compat helper, or deprecation path was added; `grep` for a legacy registration path in [`django_strawberry_framework/scalars.py`][scalars] finds none. This Decision is intact at `HEAD`.

## Decision 6 — Remove the `warnings.catch_warnings()` suppression block

Spec text: [Decision 6][spec-025-d6]. Contract that stays: the `warnings.catch_warnings()` suppression block and the `import warnings` line are gone, and the import surface is clean by construction rather than by suppression.

### Justification (moved from the spec)

- The `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload that Slice 1 switches to does NOT trigger the `DeprecationWarning` (per [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition) — verified at the Strawberry source); the suppression is no longer load-bearing.
- Keeping the suppression around "just in case" would be a documentation hazard: a future contributor reading the file would not be able to distinguish "this is here because of a real deprecation that fires" from "this is dead code from a prior migration." Removing it makes the file's contract explicit: post-migration, the import path is clean by construction.
- The existing `test_package_import_does_not_emit_strawberry_deprecation_warning` regression at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`][test-scalars] continues to pass UNCHANGED (the test runs `python -W error::DeprecationWarning -c "import django_strawberry_framework"` and asserts the subprocess exits cleanly); the test now pins the no-leak contract via the migrated registration shape rather than via the suppression block. If the suppression is accidentally restored alongside a regression in the no-warning overload, the test still catches the underlying problem.

### Alternatives considered (and rejected)

- **Leave the suppression block in place defensively.** Rejected: dead code is a maintenance hazard; the package's own regression test enforces the contract regardless.
- **Replace the suppression with a comment.** Rejected: code is the source of truth; a comment that points at a removed suppression is documentation of nothing.

### Changes this Decision underwent

- **No pre-ship change.**
- **No post-ship change.** [`django_strawberry_framework/scalars.py`][scalars] contains no `import warnings` and no `catch_warnings` at `HEAD`, and [`tests/test_scalars.py`][test-scalars]'s `-W error::DeprecationWarning` subprocess regression still carries the no-leak contract. Intact.

## Decision 7 — Test placement and shape

Spec text: [Decision 7][spec-025-d7]. Contract that stays: the factory and round-trip tests extend [`tests/test_scalars.py`][test-scalars] (the mirror partner of [`scalars.py`][scalars]) with one pytest item per test and no `parametrize` fan-out; no `tests/test_config.py` is added. The Decision's defense-in-depth note stayed in the spec rather than moving here — see [Provenance of this record](#provenance-of-this-record).

### Justification (moved from the spec)

- The new code under test lives in [`django_strawberry_framework/scalars.py`][scalars] (one module); its mirror partner is `tests/test_scalars.py` (one file). Adding a new `tests/test_config.py` would violate the mirror rule because no `django_strawberry_framework/config.py` exists (and per [Decision 2](#decision-2--helper-api-shape-and-module-location), no such module is introduced).
- Adding the factory tests to the existing file keeps related test logic close: the `BigInt` parser / serializer tests and the `strawberry_config()` registration tests both ride on the same imports and same `ScalarDefinition` shape.
- Live HTTP coverage (per the live-HTTP-priority rule at [`AGENTS.md #"any line reachable via a real GraphQL query against fakeshop"`][agents]) is earned indirectly through Slice 3's [`examples/fakeshop/config/schema.py`][schema] migration: every existing `examples/fakeshop/test_query/test_*.py` test that exercises the project schema also exercises the helper (because `config=strawberry_config()` is now called at module-import time when the project schema is constructed). A schema-construction failure in the helper would break every live HTTP test that imports the schema, so the integration is exercised end-to-end without adding new `test_query/` test files. This matches [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] Decision 6's transitive-coverage posture for axis 2 (`OptimizationPlan.apply` `_db` preservation verified by the live HTTP test seeded-rows assertion).
- The two integration tests in `tests/test_scalars.py` — `test_bigint_serializes_int_via_strawberry_config_schema` and `test_bigint_parses_decimal_string_via_strawberry_config_schema` — pin the schema-execution path in-process so a regression at the schema-construction layer is caught at the `tests/test_scalars.py` tier. They construct a minimal `strawberry.Schema(query=..., config=strawberry_config())` with a `BigInt`-annotated resolver, run a query / mutation through `schema.execute_sync(...)`, and assert on the JSON output.

### Alternatives considered (and rejected)

- **New `tests/test_config.py` next to a new `django_strawberry_framework/config.py`.** Rejected per [Decision 2](#decision-2--helper-api-shape-and-module-location) (no new module).
- **Move the new tests into `tests/base/test_conf.py` because `conf.py` is the closest existing "configuration" module.** Rejected: `tests/base/test_conf.py` covers the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader; the helper has no settings dependency.
- **Add a live HTTP test in `examples/fakeshop/test_query/test_scalars.py` (new file) that exercises a `BigInt`-annotated resolver through `/graphql/`.** Rejected for `0.0.7`: the example project does not currently use `BigInt` directly (no `BigIntegerField` in the fakeshop models per the Step-5 grep). Adding a fakeshop model column just to exercise the helper is gold-plating; the in-process integration tests catch the registration-path regression at the same coverage tier.

### Changes this Decision underwent

- **No pre-ship change.**
- **Post-ship, the file grew past the pinned count** and the counts the Decision states are stale in both directions. See [D7](#d7--the-test-counts-are-stale-in-both-directions).
- **Post-ship, this Decision's third rejected alternative was reversed by a later card.** The live `/graphql/` `BigInt` test it declined for `0.0.7` now exists, on a fakeshop app that did not exist when the alternative was rejected. See [D8](#d8--the-live-test-rejection-was-reversed-by-done-026-007).

### Claims this Decision may no longer make

- That "fifteen pytest items total" are added to the file and that it therefore carries "22+15 = 37+" tests. It carries 53 `def test_` items at `HEAD`.
- That a live HTTP `BigInt` test is "Rejected for `0.0.7`" because "the fakeshop models do not include `BigIntegerField`". Both halves are false at `HEAD`; the reason the rejection gave stopped being a fact.

## Decision 8 — Version posture: this card ships inside the `0.0.7` cut

Spec text: [Decision 8][spec-025-d8]. Contract that stays: this card does not bump `__version__`, `pyproject.toml`, or the pinned version assertion; the bump belongs to whichever card ships last in a cut.

### Justification (moved from the spec)

- The `[Unreleased]` section in [`CHANGELOG.md`][changelog] already accumulates entries for the next patch — Changed bullets for the `manage.py export_schema` UX cleanup, a Fixed bullet for OSError wrapping. Per "Keep a Changelog" convention (followed by this repo), the section is the natural home for any new entry that lands after `[0.0.7]` was sealed.
- The card body does NOT request a version bump. `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s pinned version assertion are explicitly excluded from Slice 5 — per the last-card-owns-the-bump policy [`KANBAN.md`][kanban] carried for the `0.0.7` cut (interpreted forward: the last card to ship under any future cut owns its bump). The bump from `0.0.7 → 0.0.8` is a future-cut decision.
- This card IS breaking-but-alpha-OK (per [Decision 5](#decision-5--migration-posture-hard-break-in-alpha)). A breaking change joining `[Unreleased]` does NOT automatically force a version bump on this card — the cut decision is when, the bump decision is who.
- The spec filename uses `0_0_7` per the card tag (`spec-025-scalar_map_helper-0_0_7.md`) because the card is `DONE-025-0.0.7`. If a future maintainer re-tags the card to `WIP-ALPHA-020-0.0.8` (because it ended up in the 0.0.8 cut), the spec file moves with the rename — see [Risks][spec-025-risks] entry 1.

### Alternatives considered (and rejected)

- **This card bumps `__version__` to `0.0.8` and seals `[Unreleased]` under a new `[0.0.8]` heading.** Rejected: ship order is determined by which card a maintainer picks up next, not by topical fit; pinning the bump to a specific card creates a sequencing constraint that has no engineering justification. Same posture as [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] Decision 9.
- **Rename the card to `WIP-ALPHA-020-0.0.8` in [`KANBAN.md`][kanban] as part of this card.** Rejected: out of scope (the spec's boundary forbids editing [`KANBAN.md`][kanban] outside the Slice 5 column move and spec-reference rewrite); the card-tag-vs-cut mismatch is a [`KANBAN.md`][kanban] housekeeping concern resolved by whichever maintainer cuts `0.0.8`.
- **Add a separate `TODO-ALPHA-XXX-0.0.8 — 0.0.8 release cut` card to [`KANBAN.md`][kanban] that owns the bump.** Rejected per [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] Decision 9's "the 'last card to ship' policy is workable as-is" precedent.

### Changes this Decision underwent

- **No pre-ship change.**
- **The `[Unreleased]` half of this Decision never happened.** The card's three CHANGELOG bullets landed under `## [0.0.7] - 2026-05-27`, inside the cut itself. See [D1](#d1--the-card-shipped-inside-the-007-cut-not-under-unreleased).

### Claims this Decision may no longer make

- That `0.0.7` was cut on 2026-05-23. The [`CHANGELOG.md`][changelog] heading reads `## [0.0.7] - 2026-05-27`, and the ship commit `b1a6d01f` is dated 2026-05-27. The date was wrong in the spec as shipped, not merely superseded.
- That this card's entries land under `[Unreleased]` on the way to a future `[0.0.8]`, and that a re-tag to `WIP-ALPHA-020-0.0.8` is available. Both are dead — see [D1](#d1--the-card-shipped-inside-the-007-cut-not-under-unreleased) and [D11](#d11--the-re-tag-hypothetical-is-dead-not-stale). The Decision's own heading text carries the falsified claim, which is why renaming it is a Slice 2 sweep and not a one-line edit.

## Decision 9 — Example-app migration scope

Spec text: [Decision 9][spec-025-d9]. Contract that stays: the card's fakeshop migration is the one schema the project serves at `/graphql/`, [`examples/fakeshop/config/schema.py`][schema], and nothing else; the per-app schemas are audit-only because they construct no schema. Stated that way deliberately — as this card's scope rather than as a count of the project's construction sites, which is the half of the original phrasing [D14](#d14--fakeshop-gained-a-second-schema-construction-site) retired.

### Justification (moved from the spec)

- The migration's surface for the example app is exactly one `strawberry.Schema(...)` call. Touching more than that one site is gold-plating.
- The fakeshop models do not use `BigIntegerField` or `PositiveBigIntegerField` today (verified via `grep -rn "BigInt" examples/fakeshop/` — no matches). The example schema does not currently exercise `BigInt` at all; the migration of the `Schema(...)` call is a forward-looking demonstration of the new pattern, not a regression-driven change.
- Adding a fakeshop model column that uses `BigIntegerField` just to exercise `BigInt` through the new helper is out of scope for this card — the helper's correctness is exercised by the in-process integration tests in `tests/test_scalars.py` (per [Decision 7](#decision-7--test-placement-and-shape)).
- Same posture as [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] Decision 4 (the fakeshop schemas are NOT decorated with multi-db routing because routing is consumer-shaped) and [`docs/SPECS/spec-020-list_field-0_0_7.md`][spec-020] Decision 9 (the fakeshop `DjangoListField` demonstration was added as a *sibling* root field rather than rewriting existing schema entries) and [`docs/SPECS/spec-021-apps-0_0_7.md`][spec-021] Decision 7 (no fakeshop `INSTALLED_APPS` change for the AppConfig card).

### Alternatives considered (and rejected)

- **Add a `BigIntegerField` column to a fakeshop model and a corresponding `id: BigInt`-style query in the schema to exercise the round-trip live.** Rejected: out of scope; the helper's correctness is exercised by the in-process tests, and adding a model column is a model-shape decision that belongs in its own card if there is real fakeshop demand for it.
- **Skip the [`examples/fakeshop/config/schema.py`][schema] update because the fakeshop schemas don't use `BigInt`.** Rejected: the example project is the package's primary documentation surface for "what consumer code looks like"; leaving it on the pre-migration pattern would confuse readers who copy from it.

### Changes this Decision underwent

- **No pre-ship change.**
- **Post-ship, the construction call itself changed shape** — `DjangoSchema(...)` replaced `strawberry.Schema(...)`, and the optimizer extension became a factory. `config=strawberry_config()` survived both changes untouched, which is the part this Decision owns. See [D9](#d9--the-fakeshop-constructor-is-djangoschema-and-the-optimizer-is-a-factory).
- **Post-ship, the premise of the Decision's second justification bullet was removed.** fakeshop now has `BigIntegerField` columns. See [D8](#d8--the-live-test-rejection-was-reversed-by-done-026-007).
- **Post-ship, the tree grew a second non-test schema-construction site**, so the Decision's identification of its target by *count* was rewritten as an identification by *role* — the schema the project serves at `/graphql/` — with the question of which other schemas owe the registration handed to [Decision 5](#decision-5--migration-posture-hard-break-in-alpha)'s rule. The conclusion the Decision reached did not change. See [D14](#d14--fakeshop-gained-a-second-schema-construction-site).

### Claims this Decision may no longer make

- That "the fakeshop models do not use `BigIntegerField` or `PositiveBigIntegerField` today (verified via `grep -rn "BigInt" examples/fakeshop/` — no matches)". `apps/scalars/models.py` carries `signed_big` and `unsigned_big`; `apps/library/models.py` carries `lifetime_fines_cents`. The grep was a true measurement of a tree that no longer exists — which is the standing reason a grep quoted in a spec is a claim with an expiry date.
- That adding such a column is "out of scope for this card ... a model-shape decision that belongs in its own card". The scope boundary held exactly as written: it became its own card, `DONE-026-0.0.7`, and that card did it.
- That [`examples/fakeshop/config/schema.py`][schema] is "the project's sole schema-construction site", or that "schema construction happens once, in `config/schema.py`". [`examples/fakeshop/strategy_schemas.py`][strategy-schemas] is a second non-test site. The Decision may still say the card's fakeshop edit is that one served schema — that is a statement about its own scope, which nothing later moved — but it may not describe the project by a count of construction calls. See [D14](#d14--fakeshop-gained-a-second-schema-construction-site).

## Borrowing posture — explicitly do not borrow

Moved from the spec's `### Explicitly do not borrow` subsection. The spec keeps the factual half of its borrowing posture — that neither `strawberry-django` nor `graphene-django` ships a `StrawberryConfig`-bundling helper to model on, each with the grep or the mechanism that establishes it — and keeps a pointer here. What moved is the reasoning for refusing three shapes the package could have borrowed from itself.

- A `dst.Schema(query=..., ...)` wrapper that pre-populates `config=`. Rejected: shadows the upstream `strawberry.Schema` symbol, hides composition, and creates an opaque "what is this returning?" question for every consumer. Compare: the package already ships `DjangoOptimizerExtension` as an extension consumers pass via the `extensions=[...]` kwarg explicitly; the same posture (explicit composition, not wrapped construction) extends to the config kwarg.
- A static `SCALAR_MAP: dict[object, ScalarDefinition]` re-export consumers `**`-spread into their own `StrawberryConfig`. Rejected: forces every consumer to spell out `StrawberryConfig(scalar_map={**SCALAR_MAP, ...})`, with the spread pattern being unidiomatic at consumer-write time and the conflict-resolution policy (silently override or raise) becoming the consumer's responsibility. The factory keeps that policy in one place — see [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions).
- A package-level `STRAWBERRY_DEFAULT_CONFIG: StrawberryConfig` module-level constant. Rejected: a single module-level `StrawberryConfig` instance would be shared mutable state across every consumer schema; mutations to the `scalar_map` of one schema's `StrawberryConfig` would leak to every other. The factory returns a fresh instance per call so call sites are independent — see [Decision 2](#decision-2--helper-api-shape-and-module-location).

The third bullet is the one that later mattered most: it rejects a module-level `StrawberryConfig` constant on shared-mutable-state grounds, which is the same argument [Decision 2](#decision-2--helper-api-shape-and-module-location) makes for a factory. The two are one decision stated twice, and the surviving spec text keeps it once, in the Decision.

## Deliberation moved from the risks section

The spec's [Risks and open questions][spec-025-risks] section carried eight items, each in the shape "statement of the risk, `Preferred answer:` …, `Fallback:` …". The statements are live constraints and stay in the spec; the eight preferred-answer / fallback pairs are contingency reasoning and are here, in the spec's bullet order. Two of them are dead rather than merely deliberative, and are marked.

1. **`DONE-025-0.0.7` card-tag versus the already-cut `[0.0.7]` heading.** Preferred answer: the spec filename uses `0_0_7` per the card tag (`spec-025-scalar_map_helper-0_0_7.md`); the `CHANGELOG.md` entry uses `[Unreleased]`; the [`KANBAN.md`][kanban] maintainer reconciles the tag-vs-cut mismatch when they cut `0.0.8` (re-tagging the card body and the spec filename to `0_0_8` is a one-line edit that does not affect any production behavior). Fallback: if the maintainer decides to ship the spec under a `WIP-ALPHA-020-0.0.8` tag before Slice 5 lands, the spec filename moves to `docs/spec-020-scalar_map_helper-0_0_8.md` in the same commit; production-code surface is unaffected because the spec's content is version-agnostic except for the filename.
2. **`KANBAN.md` card body names `docs/spec-scalar_map_helper.md`; spec ships as `docs/spec-025-scalar_map_helper-0_0_7.md`.** Preferred answer: Slice 5 rewrites the card body's `Definition of done` bullet 1 to point at the structured name; the Step-8 archive pass at the end of the NEXT.md flow propagates the rename to any other cross-references. Fallback: if a future agent confused by the rename creates a second `docs/spec-scalar_map_helper.md`, the structured filename's content takes precedence; the stray file is deleted in a follow-up cleanup card.
3. **Strawberry's no-warning overload signature stability.** Preferred answer: the package pins Strawberry to a version that supports this overload via [`pyproject.toml`][pyproject]; a regression in the overload signature is caught by `test_strawberry_config_default_scalar_map_includes_bigint` (and the wider `test_bigint_*` parser/serializer suite) at CI time. Fallback: if Strawberry deprecates the no-class overload in a future release (extremely unlikely; it's the documented replacement for the old deprecated overload), the package re-evaluates — but pinning Strawberry's recommended path is the right answer today.
4. **`isinstance(value, BigInt)` is not supported by `NewType`.** Preferred answer: this is not a regression — consumers should not have been calling `isinstance(x, BigInt)` because `NewType` runtime semantics are documented at the Python typing level. The package does NOT advertise `BigInt` as isinstance-checkable in any [`docs/GLOSSARY.md`][glossary] entry. Fallback: if real consumer breakage surfaces (extremely unlikely for an alpha package's first-defined scalar), a follow-up card could add an `is_bigint(value) -> bool` helper, but `0.0.7` does not need it.
5. **`extra_scalar_map` collisions with future package-defined scalars.** Preferred answer: this is a non-issue today; the `Upload` card will document the addition in its own CHANGELOG entry and the collision-error message names the offending key clearly. Fallback: none needed; the consumer collision space is empty by construction in `0.0.7`.
6. **Strawberry version pin compatibility.** Preferred answer: this is the documented Strawberry path; the package's `pyproject.toml` Strawberry constraint already requires a version where this exists. Fallback: if [`pyproject.toml`][pyproject] is updated post-merge to allow an older Strawberry, the Slice 2 tests catch the regression at CI time.
7. **The example fakeshop schema does not exercise `BigInt`.** Preferred answer: the helper's correctness is exercised by the in-process integration tests in `tests/test_scalars.py` per [Decision 7](#decision-7--test-placement-and-shape) — `test_bigint_serializes_int_via_strawberry_config_schema` and `test_bigint_parses_decimal_string_via_strawberry_config_schema` construct an in-process schema that exercises the round trip; the live HTTP path is exercised transitively (every fakeshop test that imports `config.schema` runs the helper at module-import time). Fallback: a future card may add a `BigIntegerField` column to a fakeshop model and a `BigInt`-annotated resolver to a fakeshop app schema, but that is a model-shape decision outside this card's scope.
8. **Suppression-removal regression detection.** Preferred answer: post-migration, the test continues to pass because the new registration path does not emit the warning at all; the test pins the contract regardless of which mechanism (suppression or no-warning overload) produces a clean import. Fallback: if a future Strawberry change reintroduces a deprecation along the `strawberry.scalar(name=..., ...)` overload path, the regression test catches it at CI time and the package adapts in a follow-up card.

**Item 1's fallback is dead.** The `WIP-ALPHA-020-0.0.8` re-tag it contemplates cannot happen — see [D11](#d11--the-re-tag-hypothetical-is-dead-not-stale).

**Item 7's fallback has already happened, and item 5's premise is void.** `DONE-026-0.0.7` added the `BigIntegerField` column and the live `BigInt` coverage item 7 deferred (see [D8](#d8--the-live-test-rejection-was-reversed-by-done-026-007)); item 5 reasons about `_PACKAGE_SCALAR_MAP` growing an `Upload` entry, which never happened and cannot (see [D3](#d3--the-upload-forward-compatibility-prediction-was-wrong-in-mechanism)).

## Facts re-verified as still true at HEAD

Recorded so a future reader can separate "still true" from "not checked". Both were re-read against source by this cycle's pre-dispatch pass, not carried forward on the spec's word.

- **Decision 3's no-warning-overload claim holds.** [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar] still returns a `ScalarDefinition` directly, and the `DeprecationWarning` still lives only on the `cls is not None` path (`#"Passing a class to strawberry.scalar"`). Re-verified at `strawberry-graphql 0.323.2`, the version resolved in the shared `.venv` — **not** the declared floor, which is `strawberry-graphql>=0.316.0` per [`pyproject.toml`][pyproject]. The claim is therefore verified at the top of the supported range; the floor end rests on the overload having predated `0.262.0`, the constraint in force when the spec was written.
- **Decision 4's `ValueError`-not-`ConfigurationError` choice holds.** [`django_strawberry_framework/scalars.py`][scalars] raises plain `ValueError` at both `strawberry_config` rejection sites, and [`docs/GLOSSARY.md`][glossary]'s [`ConfigurationError`][glossary-configurationerror] entry is still scoped to type-creation and finalization errors, so the reasoning that separated the two exception classes is still the reasoning the code follows.

## Post-ship divergence record (D1-D14)

Fourteen places where the spec makes a present-tense claim that is false at `HEAD`. Each is keyed to the spec heading it touches, states the claim, states what is true, and names the commit or card responsible. **Nothing was skipped in the code**: the ship commit `b1a6d01f` delivered every Definition-of-done item and the shipped [`scalars.py`][scalars] matched the spec's pinned code block byte-for-byte, so every entry below is post-ship drift, not a build gap. Two entries — [D3](#d3--the-upload-forward-compatibility-prediction-was-wrong-in-mechanism) and [D5](#d5--the-spec-specified-a-fail-open-shape-not-merely-tolerated-one) — record reasoning that was **wrong in mechanism**, not merely superseded; the rest are drift. [D14](#d14--fakeshop-gained-a-second-schema-construction-site) is drift of the kind worth naming separately: the tree grew a surface the spec had counted, while the rule the spec established propagated to that surface unprompted.

The catalog was assembled in two passes, and the boundary matters when reading any count in this file: D1-D13 were derived and discharged by Slice 2; D14 was found afterwards, when the final gate's deferred-work catalog was re-derived, and discharged by Slice 3.

### D1 — the card shipped inside the `0.0.7` cut, not under `[Unreleased]`

Spec surfaces: the header `Target release:` line, [Decision 8][spec-025-d8], [Slice checklist][spec-025-slice-checklist] Slice 5, [Definition of done][spec-025-dod] items 16 and 17, [Risks][spec-025-risks] item 1.

The spec says the card lands under `[Unreleased]` for promotion to `[0.0.8]`, and that `0.0.7` was cut on 2026-05-23. Both are false. The three bullets landed under `## [0.0.7] - 2026-05-27` in [`CHANGELOG.md`][changelog]; the card shipped **inside** the cut, as one of the seven `0.0.7` cards [`KANBAN.md`][kanban] records, with the tag `0.0.7` at commit `72f6cd9`. [`docs/GLOSSARY.md`][glossary]'s index row reads `shipped (0.0.7)`, not the `shipped ([Unreleased])` placeholder the spec pins for it. Attribution: ship commit `b1a6d01f`.

The date is worth separating from the posture: `2026-05-23` was not superseded by later work, it was **wrong in the spec as shipped** — the heading it cites has always read `2026-05-27`.

**Resolved in the spec (Slice 2).** The header `Target release:` line now says the card ships inside the joint `0.0.7` cut with its entries under `## [0.0.7] - 2026-05-27`; [Decision 8][spec-025-d8] was **renamed** (`Version posture: this card ships inside the `0.0.7` cut`) and rewritten to state the joint-cut contract, and the rename moved its slug, so all 7 in-page uses in the spec and both `spec-025-d8` sites here moved with it in the same pass. The Slice 5 CHANGELOG bullet, the three `## Doc updates` CHANGELOG bullets, the `AGENTS.md` permission sentence in [Project conventions][spec-025-key-glossary], the GLOSSARY index-row and entry-status pins, and [Definition of done][spec-025-dod] 16 and 17 all now name the shared `[0.0.7]` section and `shipped (`0.0.7`)`; [Risks][spec-025-risks] item 1 became the live constraint (six sibling cards share the heading) instead of the dead posture. The word `Unreleased` no longer occurs in the spec. Decision 8 also **dropped the false `__version__` claim** — the version is `0.0.14` at `HEAD`, so "the `__version__` is pinned at `0.0.7`" was a second, uncatalogued falsehood in the same paragraph; the rewrite states only what the card does not touch.

### D2 — `scalars.py` now declares a module `__all__`

Spec surfaces: [Decision 3][spec-025-d3]'s pinned code block, [Slice checklist][spec-025-slice-checklist] Slice 1's import-surface sub-bullet.

The pinned block and the import-surface bullet enumerate the module's surface exhaustively and include no module-level `__all__`. At `HEAD` the module opens with `__all__ = ["BigInt", "Upload", "UploadDefinition", "strawberry_config"]`. Attribution: spec-037 (`4a25bf42` / `aec1bd4e` / `66d01b4a`).

**Resolved in the spec (Slice 2).** The pinned block in [Decision 3][spec-025-d3] no longer implies an exhaustive module surface, and a following sentence states that the module declares an `__all__` to which this card contributes `BigInt` and `strawberry_config`. The Slice 1 import-surface sub-bullet says the same and was retitled "Import and module surface". Neither site enumerates the full `__all__`: the module is shared with later scalar work, so an enumeration would only go stale again — the same trap [D10](#d10--the-enumerated-__all__-tuple-is-stale-the-rule-it-rests-on-is-not) records for `__init__.py`.

### D3 — the `Upload` forward-compatibility prediction was wrong in mechanism

Spec surfaces: [Non-goals][spec-025-non-goals] item 3, [Decision 2][spec-025-d2]'s module-location justification (moved to this file, and retracted under [Decision 2](#decision-2--helper-api-shape-and-module-location)), [Risks][spec-025-risks] item 5.

The spec says the helper is built so the `Upload` card "slots in by appending to `_PACKAGE_SCALAR_MAP` and re-exporting `Upload` from `__init__.py` — no other change to `strawberry_config(...)` is needed", and Risks item 5 reasons about a consumer collision on an `Upload` key once `_PACKAGE_SCALAR_MAP` "grows a second entry".

**`_PACKAGE_SCALAR_MAP` never grew a second entry, and cannot.** `Upload` is Strawberry's own `NewType("Upload", bytes)`, already present in `DEFAULT_SCALAR_REGISTRY`, so an `Upload`-annotated field resolves in **any** schema — including one built with no package config at all. The card re-exported the upstream symbol and added **no** map entry. Two tests pin exactly that, deliberately, as the contrast against the package-custom `BigInt`: [`tests/test_scalars.py::test_strawberry_config_scalar_map_excludes_upload`][test-scalars] asserts the absence, and `::test_upload_field_resolves_under_plain_strawberry_config` asserts an `Upload` field resolves without one. The module docstring in [`scalars.py`][scalars] states the same contrast in prose. Attribution: spec-037.

So the *outcome* the Non-goal promised held — no change to `strawberry_config` was needed when `Upload` landed — while the *mechanism* it named was wrong. That distinction is the whole content of this entry: a prediction that is right for the wrong reason reads as verified, and the reason it gave is now pinned by tests as the thing that does **not** happen. Risks item 5's collision reasoning is void for the same reason: a key that is never in the package map can never collide with it.

**Resolved in the spec (Slice 2).** Five surfaces were rewritten to the mechanism that is actually true: the [Key glossary references][spec-025-key-glossary] `Upload` bullet, [Goals][spec-025-goals] item 2, [Problem statement][spec-025-problem-statement] cost 2, the [Non-goals][spec-025-non-goals] `Upload` bullet, and the [Out of scope][spec-025-out-of-scope] `Upload` bullet. The forward-compatibility promise is now stated as the requirement it actually was — a registration point that needs no API change to accommodate a later scalar — and satisfied two ways: a package-**custom** scalar gains a `_PACKAGE_SCALAR_MAP` entry, while a scalar Strawberry's `DEFAULT_SCALAR_REGISTRY` already carries needs **none**. [Risks][spec-025-risks] item 5 was rewritten from the void `Upload`-collision hypothetical into the real rule (a key becomes collision-prone only when it enters the package map), which keeps the risk and drops the wrong instance of it.

### D4 — `_parse_bigint` and `_serialize_bigint` are no longer "unchanged from `0.0.6`"

Spec surfaces: [Definition of done][spec-025-dod] item 2, [Decision 3][spec-025-d3]'s third justification bullet (moved to this file, and retracted under [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition)).

Both bodies were hardened against hostile subclasses: `int.__int__(value)` so an `int` subclass cannot hand a resolver a value carrying its own `__int__`; `str.__str__(value)` before the regex so a `str` subclass cannot alter what is accepted; `int.__str__(value)` on the serialize path so the wire format stays canonical decimal; `_safe_arg_repr` / `_safe_type_name` in the messages; and `# noqa: TRY004` on the bool raise with a comment explaining the uniform-`ValueError` contract. **The wire format is unchanged** — decimal string in, decimal string out, same accept-sets — which is the part the `0.0.6` predecessor contract actually pinned. Attribution: `f274b2a4` (REVIEW `0.0.7` corrections) and `dc00f4a6` (hostile-metadata guard).

**Resolved in the spec (Slice 2).** [Definition of done][spec-025-dod] item 2 now pins what the predecessor contract actually pins — the `0.0.6` **wire format**, decimal string in and out with the same accept-sets — and says in as many words that the bodies are free to harden against hostile `int` / `str` subclasses and unreadable metadata. The pinned block's `# Parser and serializer unchanged from 0.0.6.` comment was replaced by a comment naming the base-descriptor normalization (`int.__int__`, `str.__str__`, `int.__str__`) and `_safe_arg_repr`, so a reader of the block sees the current contract rather than a false stability claim.

### D5 — the spec *specified* a fail-open shape, not merely tolerated one

Spec surfaces: [Decision 3][spec-025-d3]'s pinned code block, [Edge cases][spec-025-edge-cases] `#"extra_scalar_map={} is equivalent"`, [Error shapes][spec-025-error-shapes].

The pinned block contains

```python
extra = dict(extra_scalar_map) if extra_scalar_map else {}
```

which is a **truthiness test on a value that can be absent** — one of the shapes [`docs/builder/BUILD.md`][build] `### Fail-open shapes` enumerates by name. On the axis the spec worried about it was benign: an empty mapping and `None` genuinely produce the same `scalar_map`, and an edge case says so. What it was **not** benign about is the axis nobody named. Evaluating `if extra_scalar_map` calls the mapping's `__bool__`, and `dict(...)` calls its `keys()` / `__iter__`; a hostile or merely broken mapping raises from inside either, and whatever it raises escapes as itself. The factory promised a `ValueError` boundary and a consumer-supplied object could substitute an arbitrary exception for it.

At `HEAD` the shape is gone:

```python
if extra_scalar_map is None:
    extra: dict[object, ScalarDefinition] = {}
else:
    try:
        extra = dict(extra_scalar_map)
    except BaseException as exc:
        raise ValueError(
            "strawberry_config(extra_scalar_map=...) must be materializable; "
            f"got {_safe_arg_repr(extra_scalar_map)}.",
        ) from exc
```

An explicit `is None` branch distinguishes absent from empty, and the materialization guard converts "the input could not be read" into the factory's own promised exception instead of the caller's. That is `BUILD.md`'s rule applied literally: **guard the answer, not one spelling of the incoherent input.** Attribution: `dc00f4a6`, pinned by [`tests/test_scalars.py::test_strawberry_config_rejects_unmaterializable_extra_scalar_map`][test-scalars].

The record this entry exists to make: **the spec specified the fail-open shape.** It was not something an implementation slipped in past a spec that said otherwise — the shape is in the spec's own pinned code block, and the build was correct to ship it byte-for-byte. A plan-time read for the catalogued shapes is the only step in the process that could have caught it, and in `025` there was no such read, because the spec predates the requirement. `## Error shapes` still does not list the new `ValueError`, which is the visible residue.

**Resolved in the spec (Slice 2), across five surfaces.** The [Decision 3][spec-025-d3] pinned block now carries the `is None` branch, the `try` / `except BaseException` materialization guard, and `_safe_scalar_map_key_label`, followed by three bullets naming which properties of the body are contract rather than spelling — absent-is-not-falsy, the guard, and the safe label. [Error shapes][spec-025-error-shapes] gained the new `ValueError` with its message and its `from exc` chaining. [Decision 4][spec-025-d4] gained the statement that `ValueError` is the factory's **only** rejection class and that the guard is what makes that uniformity a contract rather than a coincidence. [Edge cases][spec-025-edge-cases] split the old truthiness-flavored equivalence bullet into two: the `{}`-versus-`None` equivalence as an *outcome* of an explicit `is None` test, and a new bullet for the unmaterializable mapping. The [Test plan][spec-025-test-plan] names `test_strawberry_config_rejects_unmaterializable_extra_scalar_map` as its pin. The spec no longer specifies a fail-open shape anywhere.

### D6 — the `repr` fallback is now a helper, and it *is* tested

Spec surfaces: [Edge cases][spec-025-edge-cases] `#"Collision-error message stability"`, [Decision 3][spec-025-d3]'s pinned code block.

The spec says the `repr(k)` fallback inside `getattr(k, '__name__', repr(k))` is "defensive-only" and "is not separately tested because the helper's contract is the error-raises path, not the message text for atypical keys". At `HEAD` the expression is `_safe_scalar_map_key_label(k)`, a module function that catches a raising `__name__` descriptor **and** rejects a non-`str` `__name__` before falling back to `_safe_arg_repr`. It is tested, by [`tests/test_scalars.py::test_strawberry_config_collision_message_survives_hostile_key`][test-scalars]. Attribution: `dc00f4a6`.

The original reasoning was not wrong about the contract; it was wrong about what an untested fallback costs once the key's metadata is attacker-shaped rather than merely unusual.

**Resolved in the spec (Slice 2).** The [Edge cases][spec-025-edge-cases] "Collision-error message stability" bullet was rewritten around `_safe_scalar_map_key_label`: it now names all three hostile-key cases the helper must survive (no `__name__`, a `__name__` descriptor that raises, a non-`str` `__name__`), states that none of them may turn the collision rejection into a different error, and cites both tests that pin them — `test_strawberry_config_collision_message_survives_hostile_key` and `test_scalar_collision_label_falls_back_when_class_name_metadata_is_unreadable`. The "is not separately tested" claim is gone. The pinned block carries the helper itself.

### D7 — the test counts are stale in both directions

Spec surfaces: [Decision 7][spec-025-d7], the [Test plan][spec-025-test-plan] headings, [Definition of done][spec-025-dod] item 4, [Edge cases][spec-025-edge-cases] `#"tests/test_scalars.py test count"`.

The spec pins "fifteen new pytest items" and says the file will carry "22+15 = 37+" tests. Two further factory tests landed post-ship (`test_strawberry_config_rejects_unmaterializable_extra_scalar_map`, `test_strawberry_config_collision_message_survives_hostile_key`) and spec-037 added four `Upload` pins; [`tests/test_scalars.py`][test-scalars] holds **53** `def test_` items at `HEAD` (`grep -c '^def test_'`). The fifteen-item figure is still a true statement about what *this card added*; the 37+ projection is not a true statement about anything. Attribution: `dc00f4a6`, spec-037.

**Resolved in the spec (Slice 2) by removing the projection, not by restating it.** [Decision 7][spec-025-d7], the [Test plan][spec-025-test-plan] preamble, [Definition of done][spec-025-dod] item 4 and the [Edge cases][spec-025-edge-cases] count bullet now say the card **contributes** fifteen named items and say explicitly that the file's total is not this card's to pin, because the module is shared with later scalar work. The `22+15 = 37+` projection and the two `22+` counts are deleted. The Test plan additionally names the three later items that pin the same factory's boundaries (the materialization guard and the two label fallbacks) so a reader auditing the rejection paths finds all eighteen.

### D8 — the live-test rejection was reversed by `DONE-026-0.0.7`

Spec surfaces: [Slice checklist][spec-025-slice-checklist] Slice 2's `tests/types/test_converters.py` bullet, [Definition of done][spec-025-dod] item 6a, [Decision 7][spec-025-d7]'s third rejected alternative (moved to this file), [Decision 9][spec-025-d9]'s second justification bullet (moved to this file), [Risks][spec-025-risks] `#"The example fakeshop schema does not exercise BigInt"`.

The spec enumerates ten migrated schema-construction sites in the BigInt section of [`tests/types/test_converters.py`][test-converters] and rejects a live `/graphql/` `BigInt` test for `0.0.7` on the ground that "the fakeshop models do not include `BigIntegerField`". Six of the ten no longer exist anywhere — `test_big_integer_field_maps_to_bigint_in_schema`, `..._nullable_in_schema`, `test_positive_big_integer_field_maps_to_bigint_in_schema`, `test_bigint_serializes_query_result_as_string_via_schema_execution`, `test_bigint_parses_string_argument_via_schema_execution`, `test_bigint_parses_int_argument_via_schema_execution`. They were **promoted** to live `/graphql/` coverage on a new `apps.scalars` fakeshop app ([`examples/fakeshop/test_query/test_scalars_api.py`][test-scalars-api], 29 passing), the converters file's own banner comment records the move, and four rejection / edge tests remain. `apps/scalars/models.py` now carries `signed_big = BigIntegerField` and `unsigned_big = PositiveBigIntegerField`, and `apps/library/models.py` a `lifetime_fines_cents = BigIntegerField`. Attribution: `DONE-026-0.0.7` (spec-026).

This is the live-first pattern working as intended rather than a defect: the package-tier stand-in existed because the live tier was unreachable, and the card that made it reachable retired the stand-in. What the spec may no longer say is the *reason* for the rejection, because the reason stopped being a fact.

**Resolved in the spec (Slice 2) by stating the topology rule instead of the site list.** The Slice 2 `tests/types/test_converters.py` bullet and [Definition of done][spec-025-dod] item 6a now give the migration rule — every schema-construction site in the file whose schema resolves to `BigInt` takes `config=strawberry_config()` — and say in as many words that **which** `BigInt` cases live in the package file rather than in live `/graphql/` coverage is owned by the live-coverage rule in [`AGENTS.md`][agents], not by this card. The ten-site enumeration is deleted; `test_big_auto_field_still_maps_to_int` is still named as the deliberate non-migration. The [Risks][spec-025-risks] item that rejected a live test is now the opposite claim, and a true one: the fakeshop models carry `BigIntegerField` / `PositiveBigIntegerField` columns and a live `/graphql/` query resolves `BigInt` through the factory end to end. Decision 7's defense-in-depth note was rephrased to stop counting sites.

### D9 — the fakeshop constructor is `DjangoSchema`, and the optimizer is a factory

Spec surfaces: [Decision 9][spec-025-d9], [Slice checklist][spec-025-slice-checklist] Slice 3, [Definition of done][spec-025-dod] item 7, and every `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])` example under [User-facing API][spec-025-user-facing-api].

[`examples/fakeshop/config/schema.py`][schema] builds `DjangoSchema(...)` — required for generated mutations since `0.0.14` — and the documented extension shape is a factory, `extensions=[lambda: _optimizer]`, because passing an instance is deprecated engine usage ([`docs/README.md`][readme] `#"The optimizer is a module-level singleton wrapped in a factory"`). `config=strawberry_config()` is unchanged in both, which is the only part this card's contract owns. Attribution: the spec-036 / spec-044 era.

**Resolved in the spec (Slice 2) by narrowing the claim to what this card owns.** [Decision 9][spec-025-d9], the Slice 3 bullet and [Definition of done][spec-025-dod] item 7 now say the edit is exactly two lines — the import and `config=strawberry_config()` — and that the constructor class, the roots and the `extensions=` entry are other cards' business. The `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` -> `...` before/after pair is gone from all three, along with the dead `#"strawberry.Schema(query=Query"` substring anchor it depended on. The [User-facing API][spec-025-user-facing-api] examples and the quoted `docs/GLOSSARY.md` bodies now show the documented factory shape (`_optimizer = DjangoOptimizerExtension()`, `extensions=[lambda: _optimizer]`), with one sentence saying why and that it is orthogonal to this card. Item 8 was widened from two named app schemas to every app `schema.py`, since the reason is structural. The quoted `CHANGELOG.md` bodies keep `extensions=[DjangoOptimizerExtension()]`: that is what the released `[0.0.7]` section says, and the spec quotes it accurately.

### D10 — the enumerated `__all__` tuple is stale; the rule it rests on is not

Spec surfaces: [Definition of done][spec-025-dod] items 3 and 18, [Edge cases][spec-025-edge-cases] `#"Final tuple reads:"`.

The spec pins the import line as `from .scalars import BigInt, strawberry_config` and enumerates the resulting nine-name `__all__` verbatim. At `HEAD` the line is `from .scalars import BigInt, Upload, strawberry_config` and `__all__` holds 37 names. `"strawberry_config"` is still **last** in the tuple, so the ASCII-sort rule the Decision actually rests on still holds; only the enumeration is stale. Attribution: many later cards.

**Resolved in the spec (Slice 2) by deleting the enumeration and keeping the rule.** The [Edge cases][spec-025-edge-cases] "Final tuple reads:" bullet now states the ASCII-sort rule, says the rule rather than any particular contents is the contract, and points a reader at `test_public_api_surface_is_pinned` for the actual tuple. [Definition of done][spec-025-dod] items 3, 6 and 18 dropped the "after `\"finalize_django_types\"`" positional claim — true only of the tuple as it then stood — and keep "last element" plus "widened by exactly one name", both of which still hold.

### D11 — the re-tag hypothetical is dead, not stale

Spec surfaces: [Risks][spec-025-risks] item 1's fallback (moved to this file), [Decision 8][spec-025-d8]'s second rejected alternative (moved to this file).

Both contemplate a maintainer re-tagging the card to `WIP-ALPHA-020-0.0.8` and moving the spec to `docs/spec-020-scalar_map_helper-0_0_8.md`. The 2026-07-30 board renumber gave number `020` to `DjangoListField`; this card is permanently `DONE-025-0.0.7` and its spec is at the archived structured path. The contingency has no reachable state, which is why it is deleted from the spec rather than rewritten there. Attribution: the 2026-07-30 card renumber.

**Resolved in the spec (Slice 2) by deletion, as the entry anticipated.** No `WIP-ALPHA-020-0.0.8` or `docs/spec-020-scalar_map_helper-0_0_8.md` hypothetical survives anywhere in the spec. The related `DONE-NNN` placeholder went with it: the Slice 5 KANBAN bullet, the `## Doc updates` KANBAN bullet and [Definition of done][spec-025-dod] item 15 now say the card keeps its `DONE-025-0.0.7` id, that Done-column numbers are the board's to assign in completion order, and that the spec pins the card **body**, not the number.

### D12 — every `.venv` citation points at `python3.10`, and the Strawberry floor is restated stale

Spec surfaces: the `[config]` and `[scalar]` link definitions, every inline `.venv/lib/python3.14/site-packages/...` citation in [Problem statement][spec-025-problem-statement], [Slice checklist][spec-025-slice-checklist], [Decision 3][spec-025-d3], [Edge cases][spec-025-edge-cases], and [Risks][spec-025-risks] `#"Strawberry version pin compatibility"`.

The on-disk venv is `.venv/lib/python3.14/`, so every one of those paths is dead as a citation. The pinned constraint the spec quotes, `"strawberry-graphql>=0.262.0"`, is also stale: [`pyproject.toml`][pyproject] declares `strawberry-graphql>=0.316.0` and `Django>=5.2.16`, with `requires-python >=3.10,<4.0`. Every recently reconciled spec (023, 042, 043, 044) uses `python3.14`. Attribution: dependency bumps; spec-049.

Two things must not be conflated here. The **interpreter version in a `.venv` path is an artifact of this machine's environment**, not a supported-floor statement — `requires-python` still starts at 3.10 — so re-pointing the citations at `python3.14` fixes a dead path and says nothing about support. The **floor constraint** is the separate, real correction.

**Resolved in the spec (Slice 2).** All 14 `python3.10` occurrences are now `python3.14` — the `[config]` and `[scalar]` link definitions plus every inline citation in the Problem statement, the Slice checklist, Decision 3, Edge cases, Risks and the quoted KANBAN body — and the six in this file's moved text went in the same sweep. [Risks][spec-025-risks] "Strawberry version pin compatibility" was rewritten around the declared floor: the constraint is `strawberry-graphql>=0.316.0`, the constraint rather than any resolved version is what guarantees the overload, and the venv reading is named as confirming the **top** of the supported range. The [Edge cases][spec-025-edge-cases] overload bullet says the same. The interpreter version is nowhere restated as a support claim — `requires-python` still starts at 3.10.

### D13 — the doc-side claims the spec makes about files it chose not to edit

Spec surfaces: [Slice checklist][spec-025-slice-checklist] Slice 4's `docs/TREE.md` bullet and its `docs/README.md` Relay-Node bullet, [Definition of done][spec-025-dod] items 13 and 14.

Three claims, all false at `HEAD`. [`docs/TREE.md`][tree] — script-rendered from the module docstring — no longer reads "`BigInt` public scalar" but "Public GraphQL scalars + the ``strawberry_config()`` schema-config factory", so the bullet's "the entry stays as-is since the file's role is unchanged" is doubly wrong (the role *did* change, and the line did too). Root [`README.md`][readme-repo] is no longer untouched: its `0.0.7` status bullet names `strawberry_config()`. And the [`docs/README.md`][readme] Relay Node example no longer constructs a schema at all, so the sub-bullet describing its rewrite has no target. Attribution: later doc work.

None of the three is a defect in the shipped card. DoD 13 and 14 were accurate statements of what *this* card did and did not touch; they read as false now only because they are phrased as present-tense facts about other files. That is the generic failure mode of a "file X is NOT edited" DoD item, and the reason Slice 2 rewrites them as statements about this card's scope rather than about the files' contents.

**Resolved in the spec (Slice 2) by rephrasing each claim as a statement about this card's scope.** [Definition of done][spec-025-dod] item 13 now says the card adds no module and no test file, so it owes `docs/TREE.md` no structural edit, and that `docs/TREE.md` is script-rendered from module docstrings and never hand-edited — the Slice 4 and `## Doc updates` TREE bullets say the same and cite [`scripts/build_tree_md.py`][build-tree]. Item 14 says the card edits no consumer-facing primitive name, so it owes the root `README.md` no walkthrough change, and adds that what the root README says about the `0.0.7` release line is the release notes' business. Item 10 and the `docs/README.md` bullets in Slice 4 and `## Doc updates` were re-scoped from a named-example list to a rule — every schema-construction block gains `config=`, a block that constructs no schema needs no edit — which is why the Relay Node sub-bullet's disappearance costs nothing.

### D14 — fakeshop gained a second schema-construction site

Spec surfaces: [Decision 9][spec-025-d9] first paragraph and its second paragraph's closing clause, [Risks][spec-025-risks]' live-tier bullet, and the [Current state][spec-025-current-state] bullet for [`examples/fakeshop/config/schema.py`][schema].

Four sentences state a census of the fakeshop tree: [`examples/fakeshop/config/schema.py`][schema] is "the project's sole schema-construction site", in [Decision 9][spec-025-d9] and again in the [Current state][spec-025-current-state] bullet; "schema construction happens once, in `config/schema.py`"; and Slice 3 migrates "the one fakeshop schema-construction call". All are false at `HEAD`, and the `## Current state` one is false of its own baseline too: `git grep -nE '(strawberry\.Schema|DjangoSchema)\(' b1a6d01f^ -- examples/fakeshop` returns `config/schema.py` **and** `test_query/test_multi_db.py`, so at the `0.0.6` surface the bullet describes, `config/schema.py` was the sole *non-test* site and not the sole site. That section's framing sentence scopes every bullet in **time** — to the starting surface rather than the shipped result — and time is not the axis this claim is wrong on, so the framing does not rescue it. [`examples/fakeshop/strategy_schemas.py::build_strategy_schema`][strategy-schemas] builds a second one, returning a `strawberry.Schema` over its `query_cls` argument with `config=strawberry_config()` and the strategy's extension list; the call is broken across lines in the source, so it carries no single-line substring to anchor. And it is not a test module: its own docstring declares it a shared builder importable from both the test tier and the benchmark scripts, so the two-strategy schema construction that `tests/test_lateral_pg_parity.py` and `scripts/bench_nested_fetch.py` compare against is one implementation. Non-test schema-construction sites in the project today are that file and `config/schema.py`. Attribution: commit `8fe01840` (2026-07-07, "refactor: Consolidate the optimizer's duplicated contracts (DRY pass on the fetch-strategy arc)"), which added the file; the ship commit `b1a6d01f` is an ancestor of it, so the census was true when written.

This is drift, and the reasoning behind [Decision 9][spec-025-d9] was right. The Decision's conclusion — the card's fakeshop edit is the served project schema and nothing else — is unaffected by a harness module existing; only the *description of the tree* that the Decision used to justify the conclusion decayed. **The migration rule propagated to the new site unprompted**, which is evidence for the Decision rather than against it: `strategy_schemas.py` was written six weeks after the ship commit, by an unrelated DRY pass, and it passes `config=strawberry_config()` without any card telling it to. Nor is there a code gap anywhere: no fakeshop schema resolves `BigInt` without the registration. The two fakeshop schema builds that omit `config=strawberry_config` — the seven in `test_query/test_products_visibility_api.py`, over `apps.products` types only, and `_SETUP_PROBE_SCHEMA` in `test_query/test_transport_api.py`, over a pure-Strawberry query with no Django model — resolve no `BigIntegerField` / `PositiveBigIntegerField` column, `apps/products/models.py` declaring none. That is [Decision 5](#decision-5--migration-posture-hard-break-in-alpha)'s rule holding exactly as stated: the registration is owed by a schema that resolves `BigInt`, not by every schema.

**Resolved in the spec (Slice 3) by naming the site's role and the rule's owner, not by refreshing the count.** A replacement census — "the two schema-construction sites" — would rot the same way "one" did, so [Decision 9][spec-025-d9] now identifies `config/schema.py` as *the schema the project serves at `/graphql/`*, says explicitly that the contract names that site rather than a count of the project's construction calls, and hands the question of which other schemas must carry the registration to [Decision 5](#decision-5--migration-posture-hard-break-in-alpha)'s rule and to the code that builds them. The second paragraph keeps its structural point about per-app `schema.py` modules — they declare a `@strawberry.type class Query` and construct no schema, so one added later needs no edit — with the false generalization that construction happens only in `config/schema.py` replaced by what is actually structural: an app `schema.py` contributes a `Query` root and leaves construction to whatever composes it. The [Risks][spec-025-risks] bullet keeps its whole point (the registration path is exercised over a real `/graphql/` request, and that live tier is where a registration regression surfaces first) and drops only its census, naming the served schema's construction call. The spec cites `strategy_schemas.py` nowhere: naming a second site in a contract document re-creates the rot that D10 established the rule against, and the file is not this card's to own.

The fourth surface, the [Current state][spec-025-current-state] bullet, is repaired on a different axis, because it is the only one of the four that is a deliberate statement about a **past** surface: it keeps a census — that section's whole purpose is to enumerate the baseline — and gains the tier qualifier the claim was always missing, reading "the schema the project serves at `/graphql/` — its sole **non-test** schema-construction site". Naming the site by the same role phrase the Decision now uses is what makes the two agree instead of appearing to contradict each other 270 lines apart. The census is safe here where it was not in the Decision: the `0.0.6` baseline is immutable, so a count of it cannot rot.

## Verification performed by the rationale move (Slice 1)

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` -> `OK: 17 terms - all have glossary entries and at least one spec link.` exit 0. **Unchanged from before the move**, which is the number the spec's own Definition-of-done item 9a pins: the move could have taken away a term's only spec link and did not.
- `uv run python scripts/check_trailing_commas.py --check` on the spec and this file -> exit 0, so both keep the ten-header link-definition scaffold.
- In-page anchors, both files: every `](#...)` resolved against the file's own computed heading slugs. This file: 0 unresolved. The spec: the same 10 unresolved targets as before the pass, all of them quoted `docs/GLOSSARY.md` entry text inside `## Doc updates` plus one genuine pre-existing break, `](#step-3--read-the-kanban)` inside [Decision 8][spec-025-d8]. None was introduced here and none is fixed here.
- Reference ids, both files: `used-not-defined: []`, `defined-not-used: []`, with code spans and fenced blocks stripped before the sweep. Four spec definitions were orphaned by the removals — `[spec-018]`, `[spec-019]`, `[conf]`, `[next-step-8]` — and were deleted from the spec; all four are defined here, because the moved text still uses them.
- Every link-definition path in this file was disk-exists-checked and every cross-file `#fragment` resolved against the target file's real headings: 0 failures. The spec still reports the 5 pre-existing failures it had before the pass (`[config]` / `[scalar]` under `python3.10`, the `spec-023` `#decision-9--joint-0_0_7-cut` anchor, and two `TODAY.md` fragments) — see [D12](#d12--every-venv-citation-points-at-python310-and-the-strawberry-floor-is-restated-stale) for the first two.
- Spec size: **135,777 bytes before the move, 107,692 after** — 28,085 bytes, 21% of the spec, removed from every future worker spawn's reading cost. This file was 76,619 bytes as the move left it, read only by Worker 1 and Worker 3.
- Post-move sweep: `grep -c '^Justification:'` and `grep -c '^Alternatives considered'` both report **0** in the spec, `grep -oE 'Justification[a-z ]*:' | wc -l` reports **0**, and `Preferred answer:` / `Fallback:` / `Revision history` together report **0**. Nothing that moved here also survived there.
- No `pytest`, no `--cov*` flag, no source or test file touched, no commit, no branch.

## Verification performed by the spec reconciliation (Slice 2)

- All thirteen divergences this pass acted on are discharged in the spec; each of those thirteen `### D<n>` entries above closes with the edits that discharged it. (The record's fourteenth entry, [D14](#d14--fakeshop-gained-a-second-schema-construction-site), was found after this pass closed and is Slice 3's.) Two further falsehoods surfaced in the same paragraphs and were corrected with them: [Decision 8][spec-025-d8] claimed `__version__` is pinned at `0.0.7` (it is `0.0.14`), and [Decision 1][spec-025-d1] claimed the spec file lives at `docs/spec-025-scalar_map_helper-0_0_7.md` (it is archived under `docs/SPECS/`, with companions in `docs/SPECS/appx/`).
- **Chronology sweep on the spec: clean.** `Revision 1`, `as of revision`, `as of review`, `Amendment`, `Retraction`, `review round`, `Superseded`, `archaeology`, `Unreleased`, `2026-05-23`, `0.0.8`, `DONE-NNN`, `python3.10`, `0.262.0`, `37+`, `22+` all report **0** occurrences. The surviving `no longer` / `pre-migration` / `post-migration` phrases describe the `0.0.6` -> `0.0.7` registration break, which is the card's subject, not the spec's own editing history.
- `## Current state` was given an explicit one-line framing as the `0.0.6` baseline the card starts from. It is the problem statement's baseline rather than a claim about `HEAD`, and an unframed "current state" section in a shipped spec reads as the latter.
- **Anchors and references, both files.** Spec: `used-not-defined: []`, `defined-not-used: []`, all 5 previously dead link definitions repaired (`[config]` / `[scalar]` to `python3.14`, `[spec-023-decision-9]` to the real `#decision-9--joint-007-cut` slug, and the two `TODAY.md` fragments to the renamed `#what-to-put-in-configschemapy-today` / `#whats-in-productsschemapy-today` headings, with their ref ids and visible link text renamed to match), **0** bad definition targets, **0** inline cross-file links. This file: 0 unresolved anchors, 0 bad targets, 0 inline cross-file links — one inherited inline `](../../../CHANGELOG.md)` in Decision 8's moved text was converted to the reference-style `[changelog]`, and its `#"## [Unreleased]"` substring anchor dropped, that heading no longer existing.
- **Substring citations audited, not assumed.** Every `#"..."` anchor in the spec was `grep -F`-checked against its target file: 18 distinct anchors resolve, and 3 did not — `#"Migration to a"` (4 uses; the line it cites is the one this card **removes**, so it is dead by construction), and `#"strawberry.Schema(query=Query"` against `GOAL.md` and `examples/fakeshop/config/schema.py` (4 uses; both files now break that call across lines). All 8 uses were rewritten to cite the file without a substring anchor.
- **9 unresolved in-page anchors remain in the spec, all correct as they stand.** Every one is inside quoted `docs/GLOSSARY.md` entry text in the Slice 4 checklist and `## Doc updates` (`#bigint-scalar`, `#upload-scalar`, `#specialized-scalar-conversions`, `#djangotype`, `#djangooptimizerextension`, `#strawberry_config`). They resolve in `docs/GLOSSARY.md`, which is where the quoted text lands; rewriting them would make the spec's pinned bodies differ from the file they pin. The genuine break the move deferred here, `](#step-3--read-the-kanban)`, is gone with the Decision 8 rewrite.
- **Gates.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` -> `OK: 17 terms` exit 0, the count [Definition of done][spec-025-dod] item 9a pins, unchanged by this pass. `uv run python scripts/check_trailing_commas.py --check` on both files -> exit 0. `git diff --check` on both -> exit 0. Link-definition scaffold on both: one delimiter, all 10 canonical headers in order, alphabetical by ref id within every group, each def grouped by where its **target** lives.
- No `.py` file touched, so no `ruff` run and no `pytest` — with or without a coverage flag. No commit, no branch.

## Verification performed by the Decision 9 census repair (Slice 3)

- **The finding was re-derived from source, not read off the dispatch.** `git log --diff-filter=A -- examples/fakeshop/strategy_schemas.py` names `8fe01840` as the file's only adding commit; `git merge-base --is-ancestor b1a6d01f 8fe01840` exits 0, so the census was true when written. A repo-wide `grep -rn --include='*.py' -E '(strawberry\.Schema|DjangoSchema)\('` with the `.venv` excluded returns exactly two non-test `examples/fakeshop/` hits — `config/schema.py` and `strategy_schemas.py`; every `django_strawberry_framework/` hit was opened and is a docstring example, and `config/schema.py`'s other hit is a comment.
- **No code gap.** The `config=strawberry_config` population was re-taken after the first instrument under-reported it: `config=strawberry_config()`, with the empty parens, misses `test_query/test_optimizer_auto_api.py`'s `config=strawberry_config(extra_scalar_map={BombValue: bomb_scalar})`. The two fakeshop modules that genuinely build schemas without the registration resolve no `BigInt` — verified by reading their types, and `apps/products/models.py` contains no `Big` at all.
- **Two claims the spec still makes, re-verified rather than assumed**, because a positively-spelled census is invisible to the negative-vocabulary sweep that found this one. [Slice checklist][spec-025-slice-checklist] Slice 3's "(the file's sole one)" is scoped to `config/schema.py`, whose only construction call is the module-level [`examples/fakeshop/config/schema.py #"schema = DjangoSchema("`][schema] binding; the file's one other match is a comment. [Definition of done][spec-025-dod] item 8's "every app `schema.py` ... none constructs a schema" holds over the app tree's own closed set: all six `examples/fakeshop/apps/*/schema.py` modules declare a `@strawberry.type class Query` and none constructs a schema.
- **Counts adjudicated individually, not bumped.** The record's heading and opener describe the *record*, which now holds fourteen, so both moved and the heading's slug moved with them at both use sites. [Provenance of this record](#provenance-of-this-record) and [Verification performed by the spec reconciliation (Slice 2)](#verification-performed-by-the-spec-reconciliation-slice-2) are scoped to what Slice 2 acted on and keep **thirteen**, each gaining one clause so a reader meeting fourteen entries under the heading they point at is not misled. The record's "**Nothing was skipped in the code**" sentence and its "two entries wrong in mechanism, the rest drift" sentence both stay true with D14 added: D14 is drift and carries no code gap. The spec's own five occurrences of "thirteen" were left alone — they count the factory tests, a different population that no arithmetic here touches.
- **Gates.** `check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` -> `OK: 17 terms` exit 0, the count [Definition of done][spec-025-dod] item 9a pins, unchanged by this pass. `check_trailing_commas.py --check` on both files -> exit 0. Anchors and references, both files: 0 unresolved in-page anchors introduced, `used-not-defined: []`, `defined-not-used: []`, 0 inline cross-file links, every link-definition target disk-exists-checked. Every `#"..."` substring citation this pass touched was `grep -F`-checked **in the cited file**.
- No `.py` file touched, so no `ruff` and no `pytest` — this pass changes no executable line, with or without a coverage flag. No commit, no branch.

## Verified against the shipped code

- **The code shipped the spec exactly.** This cycle's pre-dispatch pass read every Definition-of-done item against `HEAD` before dispatch: the bare `NewType`, `_BIGINT_SCALAR_DEFINITION`, `_PACKAGE_SCALAR_MAP`, the keyword-only signature, the removed suppression block, the `__init__.py` re-export with `strawberry_config` last in `__all__`, all fifteen spec-named tests, the fakeshop migration, the GLOSSARY entry and its CSV row, and the three CHANGELOG bullets. **The shipped [`scalars.py`][scalars] matched the spec's pinned code block byte-for-byte** — including the two constructs later hardening replaced. Nothing was skipped at build time, which is why this cycle changes no code and no tests. The evidence table is in [`docs/builder/build-025-scalar_map_helper-0_0_7.md`][build-025] `## Pre-dispatch verification`.
- **The focused suites are green at `HEAD`:** `tests/test_scalars.py tests/base/test_init.py tests/types/test_converters.py` -> 134 passed; `examples/fakeshop/test_query/test_scalars_api.py` -> 29 passed. Neither was run by this pass, which touches no `.py` file.
- **Every count in this file was measured at the time of writing**, with the instrument named beside it, and no count was inherited from a prior artifact without being re-derived. Three inherited figures were wrong on first statement and are recorded here at their measured values: the risks section carries **8** bullets, not 7; the nine `Alternatives considered` blocks carry **28** bullets, not 24; and the nine `Justification:` blocks carry **38** bullets (`[3, 8, 3, 4, 4, 3, 5, 4, 4]`), not 37, so **37** moved and one was retained. The third was still wrong in this file's own provenance table after the move's own correction pass and was fixed by the reconciliation slice — a corrected figure deserves no more trust than the original.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[changelog]: ../../../CHANGELOG.md
[kanban]: ../../../KANBAN.md
[pyproject]: ../../../pyproject.toml
[readme-repo]: ../../../README.md

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-upload-scalar]: ../../GLOSSARY.md#upload-scalar
[readme]: ../../README.md
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[next-step-8]: ../NEXT.md#step-8--archive-prior-specs-and-update-cross-references
[spec-017]: ../spec-017-deferred_scalars-0_0_6.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md
[spec-020]: ../spec-020-list_field-0_0_7.md
[spec-021]: ../spec-021-apps-0_0_7.md
[spec-022]: ../spec-022-export_schema-0_0_7.md
[spec-023]: ../spec-023-multi_db-0_0_7.md
[spec-025]: ../spec-025-scalar_map_helper-0_0_7.md
[spec-025-current-state]: ../spec-025-scalar_map_helper-0_0_7.md#current-state
[spec-025-d1]: ../spec-025-scalar_map_helper-0_0_7.md#decision-1--spec-filename-and-canonical-naming
[spec-025-d2]: ../spec-025-scalar_map_helper-0_0_7.md#decision-2--helper-api-shape-and-module-location
[spec-025-d3]: ../spec-025-scalar_map_helper-0_0_7.md#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition
[spec-025-d4]: ../spec-025-scalar_map_helper-0_0_7.md#decision-4--conflict-resolution-for-extra_scalar_map-collisions
[spec-025-d5]: ../spec-025-scalar_map_helper-0_0_7.md#decision-5--migration-posture-hard-break-in-alpha
[spec-025-d6]: ../spec-025-scalar_map_helper-0_0_7.md#decision-6--remove-the-warningscatch_warnings-suppression-block
[spec-025-d7]: ../spec-025-scalar_map_helper-0_0_7.md#decision-7--test-placement-and-shape
[spec-025-d8]: ../spec-025-scalar_map_helper-0_0_7.md#decision-8--version-posture-this-card-ships-inside-the-007-cut
[spec-025-d9]: ../spec-025-scalar_map_helper-0_0_7.md#decision-9--example-app-migration-scope
[spec-025-dod]: ../spec-025-scalar_map_helper-0_0_7.md#definition-of-done
[spec-025-edge-cases]: ../spec-025-scalar_map_helper-0_0_7.md#edge-cases-and-constraints
[spec-025-error-shapes]: ../spec-025-scalar_map_helper-0_0_7.md#error-shapes
[spec-025-goals]: ../spec-025-scalar_map_helper-0_0_7.md#goals
[spec-025-key-glossary]: ../spec-025-scalar_map_helper-0_0_7.md#key-glossary-references
[spec-025-non-goals]: ../spec-025-scalar_map_helper-0_0_7.md#non-goals
[spec-025-out-of-scope]: ../spec-025-scalar_map_helper-0_0_7.md#out-of-scope-explicitly-tracked-elsewhere
[spec-025-problem-statement]: ../spec-025-scalar_map_helper-0_0_7.md#problem-statement
[spec-025-risks]: ../spec-025-scalar_map_helper-0_0_7.md#risks-and-open-questions
[spec-025-slice-checklist]: ../spec-025-scalar_map_helper-0_0_7.md#slice-checklist
[spec-025-terms]: spec-025-scalar_map_helper-0_0_7-terms.csv
[spec-025-test-plan]: ../spec-025-scalar_map_helper-0_0_7.md#test-plan
[spec-025-user-facing-api]: ../spec-025-scalar_map_helper-0_0_7.md#user-facing-api

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[build-025]: ../../builder/build-025-scalar_map_helper-0_0_7.md

<!-- django_strawberry_framework/ -->
[conf]: ../../../django_strawberry_framework/conf.py
[scalars]: ../../../django_strawberry_framework/scalars.py

<!-- tests/ -->
[test-converters]: ../../../tests/types/test_converters.py
[test-scalars]: ../../../tests/test_scalars.py

<!-- examples/ -->
[schema]: ../../../examples/fakeshop/config/schema.py
[strategy-schemas]: ../../../examples/fakeshop/strategy_schemas.py
[test-scalars-api]: ../../../examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->
[build-tree]: ../../../scripts/build_tree_md.py

<!-- .venv/ -->
[config]: ../../../.venv/lib/python3.14/site-packages/strawberry/schema/config.py
[scalar]: ../../../.venv/lib/python3.14/site-packages/strawberry/types/scalar.py

<!-- External -->
