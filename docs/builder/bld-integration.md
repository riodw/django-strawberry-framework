# Build: Cross-slice integration pass — connection_field / 0.0.9 (030)

Spec reference: `docs/spec-030-connection_field-0_0_9.md`
Build plan: `docs/builder/build-030-connection_field-0_0_9.md`
Status: final-accepted

This is the BUILD.md "Cross-slice integration pass" for build 030. All five
functional slices are `final-accepted`. This artifact records the required-steps
results, the integration checks, and the findings, then specifies the one
consolidation code change the build defers to this pass (M-DRY1). A consolidation
loop is required: Worker 0 dispatches Worker 2 (build) → Worker 3 (review) →
Worker 1 (final-verify) on the `## Plan` below.

---

## Required-steps results (BUILD.md "Cross-slice integration pass")

### Step 1 — read every prior `bld-slice-*.md` in slice order

Done (all five, in order):

- `bld-slice-1-connection_base.md` (`final-accepted`) — `DjangoConnection[T]` base + `_connection_type_for` + `_build_total_count_connection` + `Meta.connection` validate/store; flagged the `"total_count"` ×3 repeated literal for this pass.
- `bld-slice-2-connection_field.md` (`final-accepted`) — `DjangoConnectionField` factory + synthesized signature + pipeline + `apply_connection_optimization` extraction; **recorded M-DRY1 as the EXPLICIT INTEGRATION-PASS DRY ITEM** (four-guard near-copy), deferred here by Worker 1's own prior decision.
- `bld-slice-3-optimizer_cooperation.md` (`final-accepted`) — TEST-ONLY, zero production change; re-affirmed M-DRY1 carry-forward.
- `bld-slice-4-live_http_export.md` (`final-accepted`) — live HTTP + public-export promotion; DRY clean, M-DRY1 untouched and still an integration-pass item.
- `bld-slice-5-doc_card_wrap.md` (`final-accepted`) — docs + card wrap; doc/DB-data only, no package logic.

### Step 2 — static inspection helper coverage

Re-ran `scripts/review_inspect.py <file> --output-dir docs/shadow` this pass for every Python file with review-worthy logic touched by the build:

| File | Touched by | Helper run this pass | Verdict |
| --- | --- | --- | --- |
| `django_strawberry_framework/connection.py` | Slices 1, 2 | yes | hotspots present but bounded; no new finding beyond M-DRY1 + the literals below |
| `django_strawberry_framework/optimizer/extension.py` | Slice 2 (extraction) | yes | one-way imports clean; `apply_connection_optimization` / `apply_to` extraction confirmed |
| `django_strawberry_framework/types/base.py` | Slice 1 | yes | `_validate_connection` added; hotspots did not worsen |
| `django_strawberry_framework/types/definition.py` | Slice 1 | yes | pure dataclass-slot addition; no logic |
| `django_strawberry_framework/list_field.py` | not edited by the build (the M-DRY1 *source* of the duplicated guards) | yes | inspected as the consolidation target/source |

`docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `TODAY.md`, `README.md`,
`CHANGELOG.md`, `KANBAN.md`, and the fakeshop schema/test files (Slices 4–5)
carry no review-worthy package logic; the helper is correctly skipped for them
(doc / DB-data / example-app surfaces). Coverage is complete.

### Step 3 — repeated string literals, cross-file comparison

Compared the **Repeated string literals** section of every shadow overview. Literals appearing in 2+ files (cross-slice DRY candidates) and intra-file repeats of note:

| Literal | `connection.py` | `types/base.py` | Other | Cross-file? | Verdict |
| --- | --- | --- | --- | --- | --- |
| `total_count` | 3× | 4× | — | **yes (2 files)** | Leave (justified below) — semantically distinct concerns in each file |
| `order_by` | 5× | — | — | no | Leave — distinct uses (resolver param name / kwarg key / `qs.order_by(...)` method) |
| `connection` | — | 2× | — | no | the `Meta.connection` key + the dataclass field name; not a magic-string candidate |
| `optimizer_hints`, `filterset_class`, `orderset_class`, `interfaces`, `nullable_overrides`, `required_overrides`, `description` | — | 2–4× | — | no | Meta-key validation strings, pre-existing pattern (not introduced by 030); consistent with `_validate_*` siblings |
| `_strawberry_schema` | — | — | `optimizer/extension.py` 2× | no | pre-existing optimizer-internal attr name; not 030 work |

The only **cross-file** literal introduced/touched by 030 is `total_count`. Decision below.

#### `"total_count"` literal decision — leave as-is (no named constant)

**Decision: do NOT introduce a named constant for `"total_count"`.** The seven
occurrences across two files split into three semantically-distinct contracts,
none of which would be made safer or clearer by a shared constant:

1. **`types/base.py` `_validate_connection` (4 sites)** — this is the **Meta sub-key validation surface**: `{"total_count": bool}` shape check, the unknown-subkey allow-set `{"total_count"}`, the bool-type check `connection["total_count"]`, and the error message. This string is the *public `Meta.connection` API contract* — the literal a consumer types in their `Meta`. Co-locating it as a literal in the validator is correct; it is the canonical place the contract is asserted.
2. **`connection.py` `_connection_type_for` (1 site)** — `connection_options.get("total_count")` reads the *stored, normalized* `definition.connection` dict. This is the same logical key as (1), but reached through the definition slot, not `Meta`.
3. **`connection.py` `_build_total_count_connection` (2 sites)** — `__annotations__ = {"total_count": int}` and the field name. This is the **Python attribute / GraphQL field name** (`total_count` → camelCase `totalCount` in the SDL), a *different* contract from the Meta sub-key: it is the connection type's output-field identifier, not the input opt-in key. They coincide by design, not by coupling.

A shared `TOTAL_COUNT = "total_count"` constant would falsely imply these are one
fact that must change together. They are three facts that happen to share a
spelling: the Meta opt-in sub-key, the stored-dict key, and the output field
name. The `0.0.9` shape recognizes exactly one sub-key, so there is no
drift-across-sites risk a constant would prevent (compare `ALLOWED_META_KEYS`,
where the *set* of keys is the abstraction, not each individual string). The
related instance-attribute name **is** already extracted (`_TOTAL_COUNT_ATTR =
"_django_total_count"` in `connection.py`) — that one warranted a constant
because it is a private implementation detail read in two helpers
(`_attach_count_sync` / `_attach_count_async`) and the field resolver, with no
external contract meaning. The carry-forward watch ("flag a constant if Slice 2
adds MORE `total_count` sites") did not trip — Slice 2 added zero new
`"total_count"` literal sites. **Verdict: leave all `"total_count"` literals
in place; no consolidation work.**

### Step 4 — imports / dependency-direction check

Compared the **Imports** section of every shadow overview and grepped the
package for cross-module edges. The one-way dependency direction holds; the
Slice-2 `_optimize` extraction introduced **no** new cross-boundary import.

- **`connection.py` imports** (local): `.exceptions`, `.filters` (`filter_input_type`), `.list_field` (`_is_async_callable`), `.optimizer.extension` (`apply_connection_optimization`), `.orders` (`order_input_type`), `.types`, `.types.relay`. Every edge points *into* shipped lower layers (filters / orders / optimizer / types / list_field). **No back-import** from any of those into `connection.py`.
- **`connection.py` → `list_field.py` already exists** (`from .list_field import _is_async_callable`, `connection.py` line 56). This is the load-bearing fact for the M-DRY1 home decision below: the connection module *already* depends on the list-field module, so lifting the shared guard validator into `list_field.py` adds **zero** new import edges and respects the existing direction.
- **`list_field.py` does NOT import `connection.py`** (grep-confirmed: no `connection` reference in `list_field.py`). The edge is strictly one-way `connection → list_field`. Putting the helper in `list_field.py` keeps it that way.
- **`optimizer/extension.py`** imports only `..registry`, `..utils.typing`, `.` (logger), `._context`, `.hints`, `.plans`, `.walker`, and stdlib/strawberry/graphql. It imports **nothing** from `connection.py` or `list_field.py`. The Slice-2 extraction (`apply_connection_optimization` + the `apply_to` shared core, with `_active_optimizer` published via a `ContextVar` in `on_execute`) is consumed *by* `connection.py` importing *from* the optimizer — the correct direction (the field cooperates with the optimizer, the optimizer does not know about the field). The extraction added one new public name to the optimizer's `__all__` (`"apply_connection_optimization"`) and no new import. **Clean.**
- **`__init__.py`** imports `DjangoConnection` / `DjangoConnectionField` from `.connection` and `DjangoListField` from `.list_field` (Slice 4 public-export promotion). Both factories sit at the same public layer; no cycle.

**Verdict: dependency direction is correct and one-way throughout; the
extraction introduced no new cross-boundary import.**

### Step 5 — walk of prior `What looks solid` / `DRY findings` / `Notes for Worker 1`

Walked all five accepted artifacts' `What looks solid`, `DRY findings`, and
`Notes for Worker 1` sections for deferred follow-up that should land here:

- **M-DRY1 (Slice 2, re-affirmed Slices 3 & 4)** — the four-guard near-copy. Explicitly recorded by Worker 1 as the "EXPLICIT INTEGRATION-PASS DRY ITEM the integration pass MUST pick up." **This is the one code item this pass resolves** — see `## Plan` below.
- **`"total_count"` ×3 literal (Slice 1, watched Slice 2)** — resolved above (Step 3): leave as-is, no new sites added.
- **L1 / L2 (Slice 1 → resolved in Slice 2)** — the double-guard run and the `total_count` resolver return-type were both fixed in Slice 2 (`_build_total_count_connection` now delegates to super first and the resolver is `-> int`). Confirmed closed; nothing to do.
- **M1 (Slice 1 → spec-edited + implemented Slice 2)** — `totalCount` over a non-queryset raises a clear `GraphQLError` (`_guard_total_count_countable`). Closed.
- **No-production-cache-clear hook (Slice 1 informational)** — the `_connection_type_cache` is cleared only in tests; production never calls `registry.clear()`. Slice 4's live usage did not surface a need for a production invalidation hook. Confirmed not needed; left as a `bld-final` deferred-work catalog note (not integration code work).
- **`types.new_class` vs `type(...)` (Slice 1 informational)** — correct primitive, no action.
- **Optimizer cooperation gap → card 033 (Slices 2–3)** — the connection-aware walker is out of scope by spec (Decision 11 / Non-goals); named in GLOSSARY; `bld-final` deferred-work catalog item, not integration code work.
- **`import_spec_terms` stricter than `check_spec_glossary` (Slice 5)** — future-spec cleanup candidate; `bld-final` deferred-work catalog item, not integration code work.

No deferred follow-up other than M-DRY1 requires code work in this pass.

---

## Integration checks (BUILD.md)

- **Duplicated helpers across slices** — ONE found: M-DRY1 (the four DjangoType-target guards duplicated between `list_field.py::DjangoListField` and `connection.py::DjangoConnectionField`). All other shared logic is genuinely reused, not copied: `filter_input_type` / `order_input_type` + the `_helper_referenced_*` orphan ledgers, the `FilterSet` / `OrderSet` `apply_sync` / `apply_async` pairs, the `_apply_get_queryset_sync` / `_apply_get_queryset_async` relay helpers, `_is_async_callable` (imported from `list_field.py`, not re-implemented), the extracted `apply_connection_optimization` (shared core with the middleware `apply_to`, not duplicated), the single-sited `_guard_first_and_last`, `_guard_total_count_countable`, `_guard_sidecar_input_against_non_queryset`, and the single-sited pipeline tail `_finalize_queryset`.
- **Inconsistent naming / error handling between slices** — consistent. Construction-time failures raise `ConfigurationError`; query-runtime failures raise `GraphQLError`. The `_validate_connection` error messages match the `_validate_filterset_class` / `_validate_orderset_class` sibling tone (`f"{meta.model.__name__}.Meta.connection ..."`). The connection-field guard messages mirror the list-field guard messages (differ only in the field-name token — which is exactly the M-DRY1 duplication).
- **Repeated ORM/queryset patterns** — centralized. The visibility→filter→order→default-order→optimizer pipeline lives once per color in `_pipeline_sync` / `_pipeline_async`, with the I/O-free tail (`_finalize_queryset`) shared. The `Manager → .all()` coercion and the `isinstance(..., QuerySet)` branch mirror `list_field.py::_post_process_consumer_*` deliberately (same contract, different field shape) — not a consolidation candidate (the connection pipeline interleaves filter/order between the steps).
- **Misplaced responsibilities between modules** — correct. The optimizer owns plan application (`apply_connection_optimization`); the connection field calls it. The validator lives in `types/base.py`; the definition stores the result; `connection.py` reads it. Once M-DRY1 lands, the shared target validator lives in `list_field.py` (the existing lower layer both factories depend on).
- **Missing / too-broad exports** — correct. Only `DjangoConnection` + `DjangoConnectionField` were promoted to `__init__.py` `__all__` (Slice 4, Decision 14). The shared `_validate_djangotype_target` helper introduced by this pass is private (`_`-prefixed) and is NOT exported — confirm in the consolidation review.
- **Repeated literals / keys / tuples** — `total_count` (cross-file, justified leave — Step 3); `order_by` / `connection` / Meta-key strings (single-file, distinct uses). No new named constant warranted.
- **Comment coherence across the new code** — coherent. The module docstrings, the Decision-cited comments, and the guard/pipeline comments tell one consistent story (Strawberry owns cursor math; the field owns visibility/filter/order/default-order/optimizer; the optimizer cooperation point is the field's because the middleware can't see the pre-slice queryset). The one comment-coherence improvement that lands naturally with M-DRY1: the duplicated guard comment blocks (the long "order is load-bearing / own-class registration check" comment exists in BOTH `list_field.py` and `connection.py`) collapse to one authoritative copy at the shared helper.

---

## Findings summary

- **M-DRY1 (Medium → resolve now):** the four DjangoType-target constructor guards in `connection.py::DjangoConnectionField` are a structurally-identical, message-aligned copy of `list_field.py::DjangoListField`'s four guards (same `inspect.isclass` → `issubclass(DjangoType)` → `definition.origin is target_type` → `callable(resolver)` sequence + same `ConfigurationError` raises, differing only in the `DjangoListField` ↔ `DjangoConnectionField` field-name token). Plus the duplicated long explanatory comment block. A third consumer (`DjangoNodeField`, card `WIP-ALPHA-032-0.0.9`) is imminent. Pre-authorized by the plan as a tightly-mirrored copy, with consolidation DEFERRED to this pass. **Resolve via the `## Plan` below.**
- **`"total_count"` cross-file literal — leave (justified, Step 3).** No code work.
- **Dependency direction — clean, one-way (Step 4).** No code work.
- **All other DRY / naming / responsibility / export / comment checks — clean.** No code work.

A consolidation loop **is** needed (M-DRY1). Artifact `Status: planned`.

---

## Plan (M-DRY1 consolidation — extract the shared four-guard target validator)

**Goal:** extract the four DjangoType-target constructor guards shared by
`DjangoListField` and `DjangoConnectionField` into one private helper both
factories call, parameterized by the factory's field-name token, preserving the
exact `ConfigurationError` message strings so all existing guard tests pass
unchanged. The fifth Relay-Node guard stays inline in `DjangoConnectionField`
(it is connection-specific).

### Helper home + signature

**Home: `django_strawberry_framework/list_field.py`** (module scope, alongside
`_is_async_callable`). Rationale (DRY-est readable home that respects one-way
dependency direction, per Step 4):

- `connection.py` **already** imports from `list_field.py` (`_is_async_callable`), so adding `from .list_field import _is_async_callable, _validate_djangotype_target` is a one-token change to an existing import line — zero new import edges, existing direction preserved.
- `list_field.py` is the lower layer (it does not import `connection.py`); the helper sitting there keeps the edge strictly one-way `connection → list_field`.
- The third consumer (`DjangoNodeField` in card 032's planned `relay.py`) will likewise import from `list_field.py` cleanly.
- A brand-new shared `_fields.py` module is NOT warranted: it would add a module for one ~15-line helper when the natural lower-layer home already exists and is already imported. (If card 032 later grows a cluster of shared field-factory helpers, *that* is the moment to consider a `_fields.py` — note it for the deferred-work catalog, but do not pre-create it now.)

**Signature:**

```python
def _validate_djangotype_target(
    target_type: type,
    resolver: Callable | None,
    *,
    field: str,
) -> None:
    """Run the four shared DjangoType-target constructor guards for a field factory.

    Shared by ``DjangoListField`` and ``DjangoConnectionField`` (and, later,
    card 032's ``DjangoNodeField``). ``field`` is the factory's public name
    (e.g. ``"DjangoListField"``) interpolated into the ``ConfigurationError``
    messages so each factory's errors name itself. Order is load-bearing — each
    check assumes the previous passed; the own-class ``definition.origin is
    target_type`` check is the strict invariant (NOT ``hasattr``). Raises
    ``ConfigurationError`` on failure; returns ``None`` when all four pass.
    The caller runs any factory-specific guards (e.g. the connection field's
    Relay-Node guard) AFTER this returns.
    """
```

The helper raises (does not return a bool); `None` return = all guards passed.
`Callable` is already imported in `list_field.py` (`from collections.abc import
Callable, Sequence`).

**Message templates (preserve EXACTLY — these are pinned by tests):**

1. `f"{field} requires a DjangoType class; got {target_type!r}."`
2. `f"{field} requires a DjangoType subclass; got {target_type.__name__}."`
3. `f"{field} target {target_type.__name__} is not a registered DjangoType. This usually means {target_type.__name__}'s \`Meta\` is missing a \`model\` declaration, or it inherits a definition from a parent without declaring its own \`Meta\`."`
4. `f"{field} resolver must be callable."`

(Template 3's wording differs trivially between the two current copies in line
*wrapping* only — the rendered string is identical. Use the wording above; both
test suites match it: the list-field tests assert the exact `DjangoListField …`
substrings, the connection tests assert field-name-agnostic substrings.)

### Implementation steps

1. **`list_field.py` — add `_validate_djangotype_target(target_type, resolver, *, field)`** at module scope (place it just above `DjangoListField`, after `_is_async_callable`). Body = the four guards in order, raising `ConfigurationError` with the `field`-parameterized templates above. Move the load-bearing explanatory comment block (the "order is load-bearing / own-class registration check / `hasattr` failure mode" comment currently inline in `DjangoListField`) into this helper as its single authoritative home.

2. **`list_field.py::DjangoListField`** — replace the inline four-guard block (`#"if not inspect.isclass(target_type)"` through the `#"resolver must be callable"` raise) with a single call: `_validate_djangotype_target(target_type, resolver, field="DjangoListField")`. Delete the now-moved comment block from `DjangoListField` (it lives in the helper now). The rest of `DjangoListField` (the resolver-shape branching, `strawberry.field(...)` return) is unchanged.

3. **`connection.py`** — extend the existing import: `from .list_field import _is_async_callable, _validate_djangotype_target` (line 56).

4. **`connection.py::DjangoConnectionField`** — replace the inline four-guard block (`#"if not inspect.isclass(target_type)"` through the `#"resolver must be callable"` raise) with a single call: `_validate_djangotype_target(target_type, resolver, field="DjangoConnectionField")`. **Keep the fifth Relay-Node guard inline** immediately after the call — it stays exactly as-is (`if not any(issubclass(iface, relay.Node) for iface in definition.interfaces): raise ConfigurationError("a connection field requires a Relay-Node-shaped DjangoType; add \`relay.Node\` to \`Meta.interfaces\`")`). Note: `DjangoConnectionField` re-derives `definition = getattr(target_type, "__django_strawberry_definition__", None)` for the Relay-Node guard AFTER the shared call — that local lookup is still needed by the inline Relay-Node guard and by the `_connection_type_for` path, so it stays (it is not part of the extracted four-guard sequence; the helper does its own internal `getattr` for guard 3). Confirm during build that `definition` is still in scope where the Relay-Node guard reads `definition.interfaces`.

5. **No export change.** `_validate_djangotype_target` is private; it must NOT be added to `list_field.py`'s `__all__` (which is `("DjangoListField",)`) or to `__init__.py`. The consolidation review's public-surface check must confirm `git diff -- django_strawberry_framework/__init__.py` is empty and `list_field.py::__all__` is unchanged.

### Tests that must still pass UNCHANGED (no edits to these)

The whole point of preserving the message templates is that no test changes:

- `tests/test_list_field.py::test_djangolistfield_rejects_non_class_argument` (asserts `r"DjangoListField requires a DjangoType class; got"`)
- `tests/test_list_field.py::test_djangolistfield_rejects_non_djangotype_class` (asserts `r"DjangoListField requires a DjangoType subclass; got NotADjangoType"`)
- `tests/test_list_field.py::test_djangolistfield_rejects_djangotype_without_definition` (asserts `r"DjangoListField target AbstractBase is not a registered DjangoType"`)
- `tests/test_list_field.py::test_djangolistfield_rejects_djangotype_subclass_without_own_meta` (asserts `r"DjangoListField target ChildCategoryType is not a registered DjangoType"`)
- `tests/test_list_field.py::test_djangolistfield_rejects_non_callable_resolver` (asserts `r"DjangoListField resolver must be callable\."`)
- `tests/test_connection.py::test_connection_field_requires_djangotype` (asserts `"requires a DjangoType class"`)
- `tests/test_connection.py::test_connection_field_requires_djangotype_subclass` (asserts `"requires a DjangoType subclass"`)
- `tests/test_connection.py::test_connection_field_requires_own_class_definition` (asserts `"not a registered DjangoType"`)
- `tests/test_connection.py::test_connection_field_rejects_non_callable_resolver` (asserts `"resolver must be callable"`)
- `tests/test_connection.py::test_connection_field_requires_relay_node` (asserts `"relay.Node"` — the inline fifth guard, unchanged)

**No new test is required** for the consolidation: the behavior is identical and
fully covered by the ten existing guard tests above (five per factory). Worker 2
should run `uv run pytest tests/test_list_field.py tests/test_connection.py
--no-cov` and confirm all guard tests pass unchanged. (If Worker 2 wants a
belt-and-suspenders unit test that `_validate_djangotype_target` interpolates the
`field=` token, that is optional and at discretion — the ten integration-level
guard tests already prove both interpolations.)

### Test moves

None. No test relocates; no test changes.

### Validation Worker 2 must run (no `--cov*`)

- `uv run ruff format .`
- `uv run ruff check --fix .`
- `uv run python scripts/check_trailing_commas.py` on the touched files (the new helper's signature has 3 params + `*` — below the 4-item threshold, so it stays inline; confirm no over-explosion).
- `uv run pytest tests/test_list_field.py tests/test_connection.py --no-cov` — the ten guard tests (plus the rest of both files) pass unchanged.
- `git status --short` — only `list_field.py`, `connection.py`, and this artifact should appear as 030-intended changes; baseline-dirty `docs/GLOSSARY.md` stays untouched.

### DRY analysis (for the consolidation)

- **Existing patterns reused:** the four guards themselves (lifted verbatim from `DjangoListField`); the existing `connection → list_field` import edge; the `ConfigurationError` raise idiom; the `field=`-parameterized-message pattern already implicit in the two copies.
- **New helper justified:** `_validate_djangotype_target` — single responsibility: run the four shared DjangoType-target constructor guards with a factory-named message. Three call sites (`DjangoListField`, `DjangoConnectionField`, future `DjangoNodeField`). This is the textbook "extract when the third consumer arrives" case — the second copy was pre-authorized as a mirror; the third (card 032) makes lockstep maintenance a real cost, so extraction now is correct.
- **Duplication risk avoided:** without this, card 032 copies the four guards a third time and any contract/message change must be made in lockstep across three factories. The helper makes the guard sequence one fact.
- **Over-abstraction avoided:** the fifth Relay-Node guard is NOT folded into the helper (it is connection-specific; folding it would force a flag parameter and re-introduce a different duplication when `DjangoNodeField` has its own fifth guard). The helper covers exactly the four genuinely-shared guards.

### Implementation discretion items

- **Exact placement** of `_validate_djangotype_target` within `list_field.py` (immediately above `DjangoListField` vs. just after `_is_async_callable`) — cosmetic; keep it near `DjangoListField`.
- **Whether to add the optional `_validate_djangotype_target` field-token unit test** — at Worker 2's discretion (the ten existing guard tests already prove both interpolations end-to-end).

Worker 1 has NOT delegated any architectural question here. The home
(`list_field.py`), the signature, the raise-vs-return shape, the message
templates, and the keep-the-fifth-guard-inline call are all fixed by this plan.

---

## Next steps for Worker 0

A consolidation loop is required. Dispatch in order:

1. **Worker 2 (consolidation build)** — implement the `## Plan` above; set `Status: built`.
2. **Worker 3 (review)** — verify the extraction is behavior-identical, messages preserved, the ten guard tests pass unchanged, no public-surface drift, the fifth guard stays inline; set `Status: review-accepted` or `revision-needed`.
3. **Worker 1 (final-verify)** — re-run the integration checks against the consolidated diff; confirm M-DRY1 is closed and no new duplication was introduced; set `Status: final-accepted`.

After this artifact reaches `final-accepted`, Worker 0 proceeds to the final
test-run gate (`bld-final.md`).

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/list_field.py` — added the shared module-scope helper `_validate_djangotype_target(target_type, resolver, *, field: str) -> None` (placed immediately above `DjangoListField`, after `_is_async_callable`); replaced `DjangoListField`'s inline four-guard block with a single `_validate_djangotype_target(target_type, resolver, field="DjangoListField")` call. The load-bearing explanatory comment block (order-is-load-bearing / own-class registration / `hasattr` failure mode) now lives once in the helper's docstring. `__all__` unchanged (`("DjangoListField",)`).
- `django_strawberry_framework/connection.py` — extended the existing import to `from .list_field import _is_async_callable, _validate_djangotype_target`; replaced `DjangoConnectionField`'s inline four-guard block with `_validate_djangotype_target(target_type, resolver, field="DjangoConnectionField")`. The fifth connection-specific Relay-Node guard stays inline, unchanged, immediately after the call. `definition = getattr(target_type, "__django_strawberry_definition__", None)` is re-derived after the helper call (the helper does its own internal lookup and returns `None`) so the inline Relay-Node guard's `definition.interfaces` read and the downstream `_connection_type_for` path still have `definition` in scope. `ruff check --fix` removed the now-unused `from .types import DjangoType` import (its only consumer was the moved `issubclass(target_type, DjangoType)` guard; `DjangoType` now appears only in docstrings/comments and is not re-exported) — a direct, expected consequence of the extraction, not unrelated churn.
- `docs/builder/bld-integration.md` — this build report; `Status:` set to `built`.

### Tests added or updated

NONE. No test edits, no new test, no test moves. The ten existing guard tests (five per factory) pass unchanged — the message templates were preserved exactly. The optional `_validate_djangotype_target` field-token unit test was not added (the ten integration-level guard tests already prove both interpolations end-to-end; declined per plan discretion).

### Validation run

- `uv run ruff format .` — 1 file reformatted (`connection.py`), 233 unchanged; re-run idempotent (234 unchanged).
- `uv run ruff check --fix .` — 1 error fixed (the unused `DjangoType` import in `connection.py`), 0 remaining; re-run `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py django_strawberry_framework/list_field.py django_strawberry_framework/connection.py` — `Fixed 0 file(s).` (the helper's 3-param + `*` signature is below the 4-item explosion threshold and stays inline, as the plan predicted).
- `uv run pytest tests/test_list_field.py tests/test_connection.py --no-cov` — **64 passed** (the full both-file run, no `--cov`). All ten guard tests pass UNCHANGED: list-field `test_djangolistfield_rejects_non_class_argument`, `…_rejects_non_djangotype_class`, `…_rejects_djangotype_without_definition`, `…_rejects_djangotype_subclass_without_own_meta`, `…_rejects_non_callable_resolver`; connection `test_connection_field_requires_djangotype`, `…_requires_djangotype_subclass`, `…_requires_own_class_definition`, `…_rejects_non_callable_resolver`, `…_requires_relay_node` (the inline fifth guard).
- `git status --short` classification: the only files I touched are `django_strawberry_framework/list_field.py` (tracked `M`) and `django_strawberry_framework/connection.py` (untracked `??`, created by a prior slice). Both are slice-intended. Every other entry in `git status --short` (`CHANGELOG.md`, `KANBAN.md`/`KANBAN.html`, `README.md`, `TODAY.md`, `__init__.py`, `optimizer/extension.py`, `types/base.py`, `types/definition.py`, `docs/*`, `examples/fakeshop/*`, the other `bld-slice-*.md`/`build-030-*.md` artifacts, `tests/*`) is baseline-dirty from Slices 1–5 at session start — NOT touched this pass. `docs/GLOSSARY.md` (baseline-dirty) left untouched per the build-wide flags. No unrelated tool churn was introduced; ruff touched only `connection.py` (reformat + the expected unused-import removal).

### Implementation notes

- **Helper home + signature (pinned by plan, confirmed in place):** `django_strawberry_framework/list_field.py` module scope, `_validate_djangotype_target(target_type: type, resolver: Callable | None, *, field: str) -> None`. Zero new import edges (`connection.py` already imported from `list_field.py`); one-way `connection → list_field` direction preserved. `Callable` was already imported in `list_field.py`.
- **Message preservation (raise-vs-return shape):** the helper raises `ConfigurationError` (returns `None` on all-pass), exactly as the plan pinned. All four templates use the `{field}` token verbatim from the plan: `f"{field} requires a DjangoType class; got {target_type!r}."`, `f"{field} requires a DjangoType subclass; got {target_type.__name__}."`, the registered-DjangoType template (with the `Meta`/`model` follow-on), and `f"{field} resolver must be callable."`. I verified the two factories' template-3 strings were token-for-token identical before extraction (they differed only in line *wrapping* and the field-name token, exactly as the plan stated) — no genuine mismatch, so nothing routed to spec reconciliation.
- **`definition` re-derivation in `connection.py`:** kept as a separate `getattr` after the helper call rather than threading it out of the helper. The helper's contract is `-> None` (guards only); the Relay-Node guard and `_connection_type_for` are not part of the shared four-guard sequence, so re-deriving the local keeps the helper single-responsibility and avoids widening its return shape.

### Notes for Worker 3

- The extraction is behavior-identical: same four guards, same order, same `ConfigurationError` raises, same rendered messages (only the `{field}` token now drives the factory name). Verify against the ten guard tests (all pass unchanged) and confirm the fifth Relay-Node guard in `DjangoConnectionField` is byte-for-byte the prior inline guard.
- Public-surface check: `git diff -- django_strawberry_framework/__init__.py` shows only the Slice-4 export-promotion baseline (DjangoConnection/DjangoConnectionField added to `__all__`) — NOT this pass's work; `__init__.py` was not edited this pass. `list_field.py::__all__` is still `("DjangoListField",)`. `_validate_djangotype_target` is private and not exported anywhere.
- One legitimate ruff side effect to expect in review: `connection.py` lost `from .types import DjangoType` because the only name-use of `DjangoType` (the `issubclass` guard) moved into the helper. `DjangoType` now appears in `connection.py` only inside docstrings/comments. This is correct and intended.
- No shadow files were used this pass.

### Notes for Worker 1

- No spec reconciliation needed. The two factories' guard messages were genuinely identical (token-for-token modulo field name and line wrapping) before extraction, so the plan's message templates applied cleanly with no mismatch. No structural drift; the home, signature, raise-shape, message templates, and keep-the-fifth-guard-inline call were all implemented exactly as the plan pinned.
- No version files, `CHANGELOG.md`, or `docs/GLOSSARY.md` touched. No public surface changed. No tests added/edited/moved.

Status updated to `built`.

---

## Review (Worker 3)

Reviewed the M-DRY1 consolidation diff (`git diff -- list_field.py`, full read of
`connection.py`) against the `## Plan` and the spec-030 guard contracts (the four
DjangoType-target guards + the Relay-Node guard). Static helper re-run on both
files (`docs/shadow`). Guard tests run without `--cov`. The bar for this pass is
identical behavior + identical error messages; that bar is met.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

**M-DRY1 is RESOLVED — duplication is gone.** The four DjangoType-target guards
now live in exactly ONE place, `list_field.py::_validate_djangotype_target`
(`list_field.py` lines 109/113/118/125 — the only `inspect.isclass(target_type)`
/ `issubclass(target_type, DjangoType)` / `definition.origin is target_type` /
`resolver must be callable` sites in the entire package; grep-confirmed). Both
factories delegate:

- `list_field.py::DjangoListField` → `_validate_djangotype_target(target_type, resolver, field="DjangoListField")`.
- `connection.py::DjangoConnectionField` → `_validate_djangotype_target(target_type, resolver, field="DjangoConnectionField")`.

No residual copy in `connection.py` (the only `connection.py` matches for the
guard idioms are the call on `connection.py::DjangoConnectionField` #"_validate_djangotype_target(target_type, resolver, field=" and a comment
reference — not a re-implementation). The long load-bearing explanatory comment
block (order-is-load-bearing / own-class registration / `hasattr` failure mode)
collapsed to its single authoritative home: the `_validate_djangotype_target`
docstring. `DjangoConnectionField` now carries only a 3-line back-reference
comment pointing at the helper. Comment story is coherent across the two modules.

**Helper home + dependency direction — clean, one-way.** The helper sits in the
lower layer (`list_field.py`), which does NOT import `connection.py` (grep:
`list_field.py`'s only `connection` token is the word "connection" inside the
helper docstring, not an import). `connection.py` → `list_field.py` already
existed (`from .list_field import _is_async_callable`); the extraction extended
that one import line to `from .list_field import _is_async_callable,
_validate_djangotype_target` (`connection.py` #"from .list_field import _is_async_callable, _validate_djangotype_target") — zero new import edges, existing
direction preserved. The third future consumer (card 032 `DjangoNodeField`) will
import from `list_field.py` the same clean way. No residual DRY concern.

### Behavior-preservation verdict

**Messages identical (modulo the `{field}` token); guard order unchanged; 5th
guard intact.**

1. **Four guards, same order, same conditions.** `_validate_djangotype_target`
   runs `inspect.isclass` → `issubclass(DjangoType)` → own-class
   (`definition is None or getattr(definition, "origin", None) is not
   target_type`) → `resolver is not None and not callable(resolver)`, in exactly
   the pre-refactor order, each assuming the previous passed. This matches
   spec-030 #"isclass → issubclass(DjangoType) → own-class `definition.origin is target_type` → callable resolver" verbatim.
2. **Message templates token-for-token identical.** The four `ConfigurationError`
   strings are the prior strings with the literal `DjangoListField` /
   `DjangoConnectionField` prefix replaced by the `{field}` parameter:
   `f"{field} requires a DjangoType class; got {target_type!r}."`,
   `f"{field} requires a DjangoType subclass; got {target_type.__name__}."`, the
   registered-DjangoType template (`f"{field} target {target_type.__name__} is
   not a registered DjangoType. …"` with the unchanged `Meta`/`model` follow-on),
   and `f"{field} resolver must be callable."`. Verified against both test
   suites: `tests/test_list_field.py` asserts the exact `DjangoListField …`
   substrings (lines 96/109/129/157/171) and `tests/test_connection.py` asserts
   the field-name-agnostic substrings (lines 405/415/426/433). All pass unchanged
   (see below) — proof the rendered strings are preserved.
3. **5th Relay-Node guard unchanged and correctly placed.** The
   `connection.py::DjangoConnectionField` #"if not any(issubclass(iface, relay.Node) for iface in definition.interfaces):"
   guard is byte-for-byte the prior inline guard (message: `"a connection field
   requires a Relay-Node-shaped DjangoType; add \`relay.Node\` to
   \`Meta.interfaces\`"`, matching spec-030 line 288). It runs AFTER the shared
   helper returns, with `definition` correctly in scope: `DjangoConnectionField`
   re-derives `definition = getattr(target_type,
   "__django_strawberry_definition__", None)` immediately after the helper call.
   This re-derivation is safe and correct — the helper's guard 3 already
   guaranteed (by raising otherwise) that `definition is not None` and
   `definition.origin is target_type` for any target that reaches the
   Relay-Node guard, so the `definition.interfaces` read can never hit `None`.
   Behavior is identical to the pre-refactor single-derivation path (the value
   is the same object); the only change is a second harmless `getattr` lookup,
   which Worker 2 correctly chose over widening the helper's `-> None` contract.
   `tests/test_connection.py::test_connection_field_requires_relay_node` (asserts
   `"relay.Node"`) passes unchanged.

### Import-removal safety

**Safe — `DjangoType` is no longer a runtime NAME in `connection.py`.** Grep for
`DjangoType` in `connection.py` returns five hits, ALL inside
docstrings/comments/error-string literals: line 17 (docstring
`DjangoTypeDefinition`), line 267 (docstring), line 524 (docstring), line 534
(comment), and line 553 (the Relay-Node error-string literal `"…Relay-Node-shaped
DjangoType…"`). None is an executable reference. The only prior runtime use was
the `issubclass(target_type, DjangoType)` guard, which moved into
`_validate_djangotype_target` in `list_field.py` (where `DjangoType` is still
imported, line 19, and still used at line 113). Removing `from .types import
DjangoType` from `connection.py` therefore cannot raise `NameError`. This is a
direct, expected consequence of the extraction (ruff `--fix` removed the
now-unused import) — not unrelated churn. The connection static overview's
Django/ORM marker table confirms no `DjangoType` executable-marker line in
`connection.py`.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows ONLY the Slice-4
export-promotion baseline (`DjangoConnection` / `DjangoConnectionField` added to
`__all__` + the `from .connection import …` line) — this is pre-existing
baseline-dirty work from Slice 4, NOT this consolidation pass. The consolidation
introduced ZERO change to `__init__.py` (the new helper is private and
unexported). `list_field.py::__all__` is unchanged at `("DjangoListField",)`
(grep-confirmed, line 22). `_validate_djangotype_target` is `_`-prefixed,
private, and appears in no `__all__` anywhere. Public surface is clean for this
pass.

### CHANGELOG sanity

Not applicable; this consolidation pass did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; this consolidation pass touched no doc/release/KANBAN/archive
surface. The baseline-dirty `docs/GLOSSARY.md` was left untouched by this pass
(confirmed: not in the consolidation's two-file diff).

### What looks solid

- Single authoritative guard home; the duplication and the duplicated comment
  block are both genuinely gone. The "extract when the third consumer arrives"
  call is correct DRY judgment, not premature abstraction.
- The fifth Relay-Node guard correctly kept inline (connection-specific; folding
  it would force a flag parameter and re-introduce a different duplication when
  card 032's `DjangoNodeField` gains its own fifth guard).
- The `-> None` raise-vs-return shape keeps the helper single-responsibility; the
  `definition` re-derivation in `connection.py` is the right call over widening
  the helper's return.
- Static overview confirms the consolidation REDUCED complexity:
  `DjangoConnectionField` dropped to 1 branch node (was higher with the inline
  four-guard block). No new hotspot/marker concern in either file.
- All 64 tests in the two guard-bearing suites pass unchanged.

### Temp test verification

No temp tests created. The ten existing guard tests (five per factory) plus the
two suites' remaining tests fully pin the preserved behavior; behavior is
identical, so no new test is warranted. The plan's optional
`_validate_djangotype_target` field-token unit test was correctly declined (the
ten integration-level guard tests already prove both `field=` interpolations
end-to-end). Disposition: none needed.

Guard tests run (no `--cov`): `uv run pytest tests/test_list_field.py
tests/test_connection.py --no-cov` → **64 passed**, including all ten guard
tests (list-field `…_rejects_non_class_argument`, `…_rejects_non_djangotype_class`,
`…_rejects_djangotype_without_definition`,
`…_rejects_djangotype_subclass_without_own_meta`, `…_rejects_non_callable_resolver`;
connection `…_requires_djangotype`, `…_requires_djangotype_subclass`,
`…_requires_own_class_definition`, `…_rejects_non_callable_resolver`,
`…_requires_relay_node`).

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation needed. The consolidation is behavior-preserving: the spec
guard contracts (spec-030 lines 82/288/377–379) describe the same four-guard +
Relay-Node-guard sequence and the same messages that the consolidated diff
delivers; nothing in the spec references the implementation shape (inline vs
helper), so no spec edit is implied. The private helper is correctly unexported,
matching the Decision-14 public-export gate. Deferred follow-up for the catalog
(not this pass's work): card 032's `DjangoNodeField` becomes the third consumer
of `_validate_djangotype_target`; if a cluster of shared field-factory helpers
accretes there, a dedicated `_fields.py` home is the moment-to-consider, per the
plan's own note (do not pre-create now).

### Review outcome

`review-accepted`. M-DRY1 is resolved (duplication gone, one authoritative home,
one-way dependency direction preserved); behavior is identical (messages
token-for-token, guard order unchanged, 5th guard intact and correctly scoped);
the `DjangoType` import removal is `NameError`-safe; public surface unchanged;
all guard tests pass unchanged. Zero High/Medium/Low findings.

---

## Final verification (Worker 1)

### Summary

`Status: final-accepted`. Re-ran the integration checks against the consolidated
on-disk diff. M-DRY1 is **resolved** and **behavior is preserved**.

- **DRY resolved (no residual copy, no new duplication).** The four
  DjangoType-target guards now live in exactly ONE place:
  `list_field.py::_validate_djangotype_target` (`list_field.py` lines 109/113/118/124
  — the only `inspect.isclass(target_type)` / `issubclass(target_type, DjangoType)`
  / `origin is target_type` / `callable(resolver)` guard idioms in the package;
  grep-confirmed across both files). Both factories delegate:
  `DjangoListField` → `_validate_djangotype_target(..., field="DjangoListField")`
  (`list_field.py:144`); `DjangoConnectionField` →
  `_validate_djangotype_target(..., field="DjangoConnectionField")`
  (`connection.py:537`). The only `connection.py` matches for the guard region are
  the call site, the back-reference comment block (lines 534–536), and the
  re-derivation comment — no re-implementation. The duplicated load-bearing
  comment block collapsed to the helper's single authoritative docstring. The
  refactor introduced no new duplication; the home (`list_field.py`, the existing
  lower layer `connection.py` already imports from) added zero new import edges
  (`connection.py:56` extended one existing import line).
- **Behavior preserved.** The four `ConfigurationError` message templates are
  token-for-token the prior strings with the `DjangoListField` / `DjangoConnectionField`
  prefix replaced by the `{field}` parameter; guard order unchanged (each check
  assumes the previous passed). The fifth, connection-specific Relay-Node guard
  is intact and inline in `DjangoConnectionField` (`connection.py:551–555`,
  message `"a connection field requires a Relay-Node-shaped DjangoType; add
  \`relay.Node\` to \`Meta.interfaces\`"`), running AFTER the shared call with
  `definition` correctly re-derived (`connection.py:541`) and in scope.
- **Focused tests pass.** `uv run pytest tests/test_list_field.py
  tests/test_connection.py --no-cov` → **64 passed** (all ten guard tests — five
  per factory, including `test_connection_field_requires_relay_node` — pass
  unchanged).
- **Guards clean.** `django_strawberry_framework/__init__.py` `__all__` carries
  ONLY the Slice-4 export promotion (`DjangoConnection` / `DjangoConnectionField`),
  unchanged by this pass; `list_field.py::__all__` is `("DjangoListField",)`
  unchanged (helper is private, `_`-prefixed, unexported). Version files
  untouched: `pyproject.toml` / `uv.lock` / `tests/base/test_init.py` clean in
  `git status`; `__version__ = "0.0.8"` on disk. `CHANGELOG.md` (newest heading
  `[0.0.8]`, no version-heading promotion — only `[Unreleased]` above it) and
  `docs/GLOSSARY.md` are baseline-dirty from Slice 5, NOT touched by this
  consolidation (the consolidation diff is `list_field.py` + `connection.py` +
  this artifact only).
- **Integration coverage complete.** The artifact records the full BUILD.md
  cross-slice scan: Step 1 (all five slice artifacts read in order), Step 2
  (review_inspect helper coverage table for every review-worthy Python file),
  Step 3 (cross-file repeated-literal comparison incl. the `"total_count"`
  leave-as-is decision — three semantically-distinct contracts, no constant),
  Step 4 (imports / one-way dependency-direction check), Step 5 (walk of all
  prior `What looks solid` / `DRY findings` / `Notes for Worker 1`). No OTHER
  cross-slice DRY item remains open — M-DRY1 was the only code item, and it is
  now resolved. Remaining follow-ups (033 connection-aware walker, no-prod
  cache-clear hook, `import_spec_terms`-vs-`check_spec_glossary` anchor universe)
  are `bld-final` deferred-work catalog notes, not integration code work.

The integration pass is clean — no further consolidation loop needed. Ready for
the final test-run gate (`uv run pytest --no-cov` full sweep + `manage.py check`
+ `makemigrations --check --dry-run` + `ruff format --check .` + `ruff check .`
+ `git diff --check`).

### Spec changes made (Worker 1 only)

None. The consolidation is behavior-preserving and implementation-shaped only
(inline guards → shared private helper); the spec guard contracts (spec-030 lines
82 / 288 / 377–379) describe the same four-guard + Relay-Node sequence and the
same messages the consolidated diff delivers, and the spec references no
implementation shape. No spec edit implied; none made.

---

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
