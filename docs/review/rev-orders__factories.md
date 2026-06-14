# Review: `django_strawberry_framework/orders/factories.py`

Status: verified

## DRY analysis

- **Defer-with-trigger: cross-family Layer-6 dynamic cache lift into `utils/inputs.py`.** The filter twin (`filters/factories.py::get_filterset_class` + `_dynamic_filterset_cache` + `_make_cache_key` + `_make_hashable` + `_create_dynamic_filterset_class`) is the built-but-unconsumed Layer-6 surface; the order side ships NO Layer-6 surface at all (only the BFS subclass + a TODO comment naming the forward-reserved `_dynamic_orderset_cache` / `get_orderset_class`). There is therefore **no duplication to remove today** — the order side has zero Layer-6 code. Defer until BOTH a dynamic `OrderSet` cache is actually built AND it shares the filter side's `(model, fields, extra_meta)` keying; only then lift the common dynamic-cache machinery (cache dict + `_make_cache_key` + `_make_hashable`) into a neutral `utils/inputs.py` helper. Trigger verbatim: "the order dynamic cache lands" (the same trigger carried on `filters/sets.py` deferred-DRY bullet 2). Until then this is a single-family mechanism, not a cross-family copy.

- **None (BFS layer) — the BFS walk, collision check, idempotent cache, subclass-rejection guard, and the `(name, cls)` materialization idempotency all live single-sited in `utils/inputs.py::GeneratedInputArgumentsFactory` (`django_strawberry_framework/utils/inputs.py:277-417`); this subclass supplies only the six family hook attributes (`orders/factories.py:61-69`) and the `_build_input_triples` override (`orders/factories.py:71-79`).** The order override is a deliberate divergence from the filter twin (no operator bag — Spec Decision 8), not a near-copy to fold. Nothing in the BFS half is duplicated against the filter factory.

## High:

None.

## Medium:

### Version-pinned docstring + TODO promise a Layer-6 surface "in `0.0.9`" that did NOT ship at `0.0.9`

The module docstring (`orders/factories.py` #"deferred to ``0.0.9`` per spec-028 Decision 12", lines 14-16) and the closing TODO anchor (`orders/factories.py` #"the dynamic factory lands with the connection-field surface in ``0.0.9``", lines 89-90) both assert that Layer 6 — the dynamic `OrderSet` cache keyed by `(model, fields, extra_meta)`, with the forward-reserved symbols `_dynamic_orderset_cache` / `get_orderset_class` — "is deferred to `0.0.9`" and "lands with the connection-field surface in `0.0.9`".

We are now AT release `0.0.9` (`pyproject.toml:4` `version = "0.0.9"`, `django_strawberry_framework/__init__.py:25` `__version__ = "0.0.9"`). The promised surface did **not** ship:

- `grep -rn "get_orderset_class\|_dynamic_orderset_cache"` across `django_strawberry_framework/`, `tests/`, `examples/` returns **zero** matches. Neither forward-reserved symbol exists anywhere.
- The connection-field surface (`spec-030`) that the TODO names as the would-be consumer DID ship at `0.0.9` (`connection.py::DjangoConnectionField`), and it resolves ordering from the **already-resolved** `definition.orderset_class` sidecar directly (`connection.py` lines 870-871 `apply_sync`, 895-896 `apply_async`, 949-950 `order_input_type(definition.orderset_class)`). It never calls a dynamic factory and never builds an `OrderSet` from `model` / `fields`.

The spec is explicit that the connection-field card owned this choice: `spec-028` Decision 12 (`docs/SPECS/spec-028-orders-0_0_8.md:197`, :479, :983) deferred Layer 6 to the `0.0.9` connection-field card, which would "decide whether to design a Layer 6 fresh ... **or require an explicit `orderset_class` declaration on every connection field**." The shipped connection field chose the **explicit-declaration** path — so Layer 6 was deliberately NOT built; it is now an unrealized/abandoned design, not an in-flight `0.0.9` deliverable.

Why it matters: this is a contract-accuracy defect, not a correctness bug. The docstring directs a maintainer to expect `_dynamic_orderset_cache` / `get_orderset_class` to appear "in 0.0.9" alongside the connection field, but the connection field shipped without them. A maintainer reading this file at 0.0.9 would either (a) believe the slice is incomplete and go looking for missing wiring, or (b) build the dynamic factory under the belief the spec still mandates it — when the spec's actual resolution (explicit `orderset_class` per connection field) already shipped. This is the same version-pinned-docstring rot class flagged on `exceptions.py::OptimizerError` ("raise sites in 0.0.7") and `optimizer/extension.py` (comment "0.1.2"), promoted to **Medium** here because the rot co-occurs with a now-false "lands in 0.0.9" promise about a public-ish forward-reserved API surface (mirrors the `filters/factories.py` Medium, which flagged the inverse: a built-but-unconsumed cache whose docstring claimed a 0.0.9 consumer).

Distinction from the filters side (carry-forward calibration): on `filters/factories.py` the Layer-6 cache IS built and tested (zero consumers) and the docstring's accuracy problem was "claims a 0.0.9 consumer that doesn't exist." Here the order Layer-6 surface is NOT built at all, and the docstring's problem is "claims the surface itself lands in 0.0.9." Both reduce to: the `0.0.9` version pin is now false. No spec ambiguity remains — Decision 12 + the shipped connection field settle it, so this needs no further spec check (unlike the filters Medium, which did).

Recommended change (root-cause, version-agnostic): reword the docstring (lines 11-17) and the TODO (lines 82-90) to state the deferral without the now-elapsed `0.0.9` pin and to record the actual resolution — that the `0.0.9` connection field chose the explicit `Meta.orderset_class` declaration path (`connection.py:949-950`), so dynamic `OrderSet` generation is a **standing deferred non-goal** with no scheduled consumer (parallel to `filters/factories.py`'s "standing deferred Non-goal" wording and `spec-027` Non-goals). If a future card revives Layer 6, it gets a fresh version pin then. Do NOT re-pin to a new concrete release (`0.0.10`/`0.0.11`) speculatively — that just reintroduces the rot.

Verbatim-intent replacement for the module-docstring tail (lines 11-17), Worker 2 may adapt wording but must drop the `0.0.9` pin:

```text
The finalizer materializes the built classes as module globals at
finalize time; this module owns build-only. Layer 6 (dynamic
``OrderSet`` generation against a connection-field meta dict) is a
standing deferred non-goal per spec-028 Decision 12: the ``0.0.9``
connection field (``connection.py::DjangoConnectionField``) resolves
ordering from the already-resolved ``Meta.orderset_class`` sidecar
directly rather than auto-generating an ``OrderSet``, so the
forward-reserved symbols ``_dynamic_orderset_cache`` and
``get_orderset_class`` are NOT shipped (see the TODO anchor at the
bottom of the file).
```

And the TODO tail (lines 89-90), drop the "lands ... in 0.0.9" promise:

```text
# Slice 2 ships only the BFS layer; the dynamic factory has no shipped
# consumer -- the connection-field surface chose the explicit
# ``Meta.orderset_class`` declaration path, so this remains a standing
# deferred non-goal until a card revives it.
```

## Low:

### Module docstring says the dynamic factory "mirrors `filters/factories.py::get_filterset_class` / `_dynamic_filterset_cache`" — accurate today, but the mirror target is itself unconsumed

The TODO (`orders/factories.py:88-89`) points the reader at `filters/factories.py::get_filterset_class` / `_dynamic_filterset_cache` as the shape to mirror. That filter surface is built-but-unconsumed (the `filters/factories.py` Medium). The cross-reference is correct as a structural pointer, but a maintainer following it would land on an equally-unconsumed surface. No action needed beyond the Medium reword (which already recasts the deferral as a non-goal); flagging only so the two TODO/docstring sets are kept consistent if either is touched. Forward-looking: re-check this pointer if the filters Layer-6 cache is ever removed or wired.

## What looks solid

### DRY recap

- **Existing patterns reused.** The entire BFS half delegates to `utils/inputs.py::GeneratedInputArgumentsFactory` (`django_strawberry_framework/utils/inputs.py:277-417`): the FIFO BFS walk (`_ensure_built`, :359-394), per-class collision check (:377-385), idempotent class-level cache (`input_object_types`, `arguments` property :351-357), `_build_class_type` (:396-403), and the subclass-rejection `__init_subclass__` guard (:324-338). This file adds only the six family hook attrs (`_collision_registry_attr` / `_factory_label` / `_family_label` / `_rename_noun` / `_related_attr` / `_related_target_attr`, lines 64-69) plus the two fresh-dict caches (lines 61-62) and the `_build_input_triples` override (lines 71-79). `_build_input_triples` delegates the actual field-triple build to `orders/inputs.py::_build_input_fields` (line 79) — a single decision site shared with the runtime order shape.
- **New helpers considered.** None warranted at this granularity. The order/filter factory split is exactly two direct subclasses of the shared base (the base's `__init_subclass__` rejects a third level), so there is no third-consumer pressure to extract anything further from the BFS layer.
- **Duplication risk in the current file.** The repeated literal `orderset` (2x, lines 69 `_related_target_attr` + 70-comment / used in `clear_order_input_namespace` call wiring) is an intentional family parameter (the related-entry target attribute name), not a constant candidate — it is the order-family value of a base-parameterized hook, identical in role to the filter side's `filterset`. The `_build_input_triples` signature is byte-near the filter twin but the BODY diverges by design (no operator bag — Spec Decision 8, line 77-78); this is an intentional sibling, not a fold candidate (same calibration as the package-wide sync/async-twin and converter-ladder rules).

### Other positives

- **BFS termination is guaranteed and test-pinned (in the shared base, re-verified here).** Cycles are handled by the enqueue-time `target not in seen` gate (`utils/inputs.py:393`) plus the pop-time `if set_cls in seen: continue` gate (:372-373); `RelatedOrder(None, ...)` placeholders are skipped at enqueue (:392-394). All three are pinned by order-side tests: `test_factory_handles_cycles_via_seen_set` (`tests/orders/test_factories.py:76`), `test_factory_dedupes_double_enqueued_target_via_seen_check` (:259), `test_factory_skips_related_order_with_none_target` (:237). A finite related-order graph terminates because every node enters `seen` exactly once before its targets enqueue.
- **No cache / request-scope / process-safety concern in this file.** The two caches (`input_object_types`, `_type_orderset_registry`) are class-level build-time dicts, not request-scoped; they are reset deterministically by `registry.clear()` through the shared `utils/inputs.py::clear_generated_input_namespace` (`orders/inputs.py::clear_order_input_namespace:382-390`, which names this module + `OrderArgumentsFactory` + `_type_orderset_registry` explicitly). The collision registry is keyed by class-derived input-type name and raises `ConfigurationError` on a distinct-class clash (base :377-385), pinned by `test_factory_raises_on_two_distinct_ordersets_sharing_classname` (`tests/orders/test_factories.py:158`).
- **The BFS factory IS consumed (contrast the deferred Layer 6).** `types/finalizer.py:1284-1294` imports and drives `OrderArgumentsFactory(orderset_cls).arguments` at phase 2.5 to materialize built input classes as module globals. So the file's shipped surface (the BFS subclass) is live and exercised end-to-end; only the *dynamic* Layer-6 surface named in the docstring/TODO is absent — which is exactly what the Medium addresses.
- **The `del type_name` in `_build_input_triples` (line 78) is correct, not dead.** The order side has no operator-bag, so it does not need the type-name prefix the filter side uses to name `<T>And`/`<T>Or`/`<T>Not` operator classes; explicitly `del`-ing the unused hook argument (rather than renaming to `_`) keeps the override signature byte-aligned with the base hook (`utils/inputs.py:405-410`) and the filter twin, documenting the deliberate no-op via the adjacent comment.
- **Static overview is clean:** 0 control-flow hotspots, 0 ORM markers, 0 calls-of-interest, 2 symbols, 1 TODO (the deferred-Layer-6 anchor, which the Medium addresses). The `TYPE_CHECKING` `models` import (line 27) is `# noqa: F401 - kept for filter-side parity` — a deliberate symmetry hold, harmless.

### Summary

`orders/factories.py` is a thin (≈91-line) subclass of the shared `GeneratedInputArgumentsFactory`: it supplies the order-family hook attributes plus a `_build_input_triples` override that omits the filter side's operator bag (Spec Decision 8), and delegates all BFS / collision / cache / materialization-idempotency mechanics to the single-sited base. The BFS half is correct, terminating, and test-pinned, with no cache/request-scope/process-safety concern, and is consumed live by the finalizer. The one real finding is contract-accuracy: the module docstring (lines 14-16) and TODO (lines 89-90) version-pin the deferred Layer-6 dynamic-`OrderSet` surface to "`0.0.9`", but at `0.0.9` that surface did not ship — the `0.0.9` connection field deliberately chose the explicit `Meta.orderset_class` path (`connection.py:949-950`) over a dynamic factory (spec-028 Decision 12, settled — no spec check needed), so `_dynamic_orderset_cache` / `get_orderset_class` are absent everywhere. Recommend rewording both to a version-agnostic "standing deferred non-goal" that records the actual resolution, mirroring `filters/factories.py`. Standard three-spawn cycle (a real source docstring/comment edit is warranted — NOT shape #5). No GLOSSARY symbol-level entry exists for this module's symbols; the related `OrderSet` GLOSSARY prose carries the same `0.0.9`-pin rot ("Layer 6 deferred to `0.0.9`", GLOSSARY:919) but that is a cross-file concern forwarded to the orders folder / project pass, not a local edit.

---

## Fix report (Worker 2)

Consolidated single-spawn (docstring/comment-only, no logic change). The one real finding (the Medium) and the comment-tier Low both reduce to a docstring/TODO reword with zero executable change, so logic + comment + changelog disposition collapse into this pass.

### Files touched
- `django_strawberry_framework/orders/factories.py` module docstring (Layer-6 tail, ~lines 12-19) — replaced the now-false `0.0.9` version pin ("Layer 6 ... is deferred to ``0.0.9`` per spec-028 Decision 12; the forward-reserved symbols ... are NOT shipped in this slice") with version-agnostic "standing deferred non-goal" wording that records the actual resolution (the connection field resolves ordering from the already-resolved ``Meta.orderset_class`` sidecar rather than auto-generating an ``OrderSet``). Mirrors `filters/factories.py`'s "standing deferred Non-goal" framing.
- `django_strawberry_framework/orders/factories.py` closing TODO (~lines 85-96) — kept the `# TODO(spec-028-orders-0_0_8 Decision 12; ...)` anchor (AGENTS.md ERA001/TODO-anchor rule: reword text, do not delete the anchor); changed the anchor parenthetical `deferred to 0.0.9` → `standing deferred non-goal` and replaced the tail "the dynamic factory lands with the connection-field surface in ``0.0.9``" with "the dynamic factory has no shipped consumer -- the connection-field surface chose the explicit ``Meta.orderset_class`` declaration path, so this remains a standing deferred non-goal until a card revives it." The forward-reserved-symbol names and the `filters/factories.py` mirror cross-reference are retained.

### Symbol-absence confirmation (Medium premise)
- `grep -rn "get_orderset_class\|_dynamic_orderset_cache" django_strawberry_framework/ tests/ examples/` returns matches ONLY inside this file's own docstring (line 15) and TODO comment (lines 86-87) — i.e. prose references, zero symbol definitions and zero callers. Both forward-reserved symbols are genuinely absent everywhere. Confirmed before rewording.
- Explicit-declaration path confirmed live: `connection.py:870-871` / `895-896` (`definition.orderset_class.apply_sync/apply_async`) and `connection.py:949-950` (`order_input_type(definition.orderset_class)`) resolve ordering from the already-resolved sidecar; no dynamic factory call, no build-from-`model`/`fields`. spec-028 Decision 12 + the shipped connection field settle the deferral (no spec ambiguity remaining), so this is a STANDING-DEFERRED non-goal, not in-flight 0.0.9 work.

### Tests added or updated
- None. Pure docstring/comment edit, zero executable lines changed — no behavior to pin (consistent with the analogous `filters/factories.py` Medium reword).

### Validation run
- `uv run ruff format .` — pass / no-changes (265 files unchanged).
- `uv run ruff check --fix .` — pass (All checks passed; only the standing COM812-vs-formatter advisory warning).
- No pytest (role rule; no executable change).

### Notes for Worker 3
- No shadow file used (static overview is clean per artifact; trivial localized reword needed no AST refresh).
- Diff is docstring/comment-ONLY, NOT logic-bearing: `git diff HEAD -- orders/factories.py` touches only the module-docstring Layer-6 tail and the TODO-comment text; no statement, signature, or import changed. TODO anchor preserved.
- Low (mirror-target cross-reference to `filters/factories.py::get_filterset_class` / `_dynamic_filterset_cache`): no separate action needed — the Medium reword already recasts the deferral as a non-goal and the cross-reference pointer is left intact and accurate. Forward-looking trigger per artifact: re-check this pointer if the filters Layer-6 cache is ever removed or wired.
- GLOSSARY rot LEFT UNTOUCHED per dispatch: the `OrderSet` "Layer 6 deferred to ``0.0.9``" pin (GLOSSARY:919) and the `Meta.orderset_class` 0.0.9 pin (GLOSSARY:806) are forwarded to the orders folder / project pass, not a local edit this cycle.
- Working tree carries many pre-existing modifications from prior review cycles and other concurrent work (presumptively maintainer/other-worker per AGENTS.md #33); this cycle's edit is confined to `orders/factories.py`. `uv.lock` not modified by this pass.

---

## Comment/docstring pass

Consolidated into the Fix report above (this is a docstring/comment-only consolidated single-spawn; there is no separate logic pass to gate on).

### Per-finding dispositions
- Medium (version-pinned docstring + TODO promise a Layer-6 surface "in 0.0.9" that did not ship): FIXED. Reworded module docstring + TODO to version-agnostic "standing deferred non-goal" recording the actual resolution (explicit `Meta.orderset_class` path). `0.0.9` pin dropped from both; no speculative re-pin to a future release. TODO anchor retained per AGENTS.md.
- Low (mirror-target `filters/factories.py` pointer is itself unconsumed): NO SEPARATE EDIT — the Medium reword already recasts the deferral; cross-reference left intact and accurate; forward-looking re-check trigger recorded above.
- DRY (defer-with-trigger cross-family Layer-6 cache lift): forward-looking, no edit — order side ships zero Layer-6 code, so there is no duplication to remove today. Trigger: "the order dynamic cache lands".
- DRY (BFS layer): `None` — single-sited in `utils/inputs.py`; no edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
- AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") — the dispatch did NOT authorize a CHANGELOG edit this cycle.
- The active review plan is silent on changelog authorization for this cycle, and a per-file cycle is never the authorising scope (per-file/folder passes forward CHANGELOG drift to the project pass).
- Substantively: the edit is a docstring/comment contract-accuracy reword with zero behavior change and no consumer-visible delta. The Layer-6 surface never shipped (in any release), so there is no released-contract change to record — nothing to defer to the maintainer either. Pure documentation-accuracy fix → internal-only.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3)

### Logic verification outcome
- **Medium (version-pinned `0.0.9` docstring + TODO rot): FIXED, premise independently re-confirmed.** `grep -rn "get_orderset_class\|_dynamic_orderset_cache" django_strawberry_framework/ tests/ examples/` returns matches ONLY inside this file's own docstring (line 18) and TODO comment (lines 90-91) — i.e. prose references, ZERO definitions and ZERO callers. Both forward-reserved symbols are genuinely absent everywhere, so the "standing deferred non-goal" reword is accurate. Confirmed the explicit-declaration path live at `connection.py:949-950` (`order_input_type(definition.orderset_class)` builds the `orderBy` arg from the already-resolved sidecar) — no dynamic-factory call, no build-from-`model`/`fields`. The connection field chose the explicit `Meta.orderset_class` path (spec-028 Decision 12 resolution), so Layer 6 is correctly recast as a standing deferred non-goal with no scheduled consumer.
- **No version pin remains:** `grep -nE "0\.0\.(9|10|11)"` over the target returns NONE — version-agnostic confirmed, no speculative re-pin to a future release.
- **TODO anchor preserved (AGENTS.md ERA001/TODO-anchor rule):** the `# TODO(spec-028-orders-0_0_8 Decision 12; ...)` anchor survives at line 85; only the parenthetical (`deferred to 0.0.9` → `standing deferred non-goal`) and the tail text were reworded, matching the Fix report.
- **Mirrors `filters/factories.py`:** new docstring uses the same "standing deferred non-goal" framing as the filter twin's docstring (`filters/factories.py:14-18` "standing deferred Non-goal"); cross-reference pointer to `get_filterset_class`/`_dynamic_filterset_cache` retained and accurate.
- **Low (mirror-target pointer itself unconsumed): NO SEPARATE EDIT, accepted.** The Medium reword already recasts the deferral; cross-reference left intact with the forward-looking re-check trigger recorded. Correct disposition.
- **Diff is docstring/comment-ONLY:** `git diff 0872a20 -- orders/factories.py` touches only the module-docstring Layer-6 tail and the TODO-comment text — no statement, signature, or import changed. Confirmed against source: executable lines (the `OrderArgumentsFactory` body + 6 hook attrs + `_build_input_triples` override) are byte-unchanged from baseline.

### DRY findings disposition
- Defer-with-trigger (cross-family Layer-6 cache lift into `utils/inputs.py`): correctly forward-looking — the order side ships ZERO Layer-6 code (grep-confirmed), so there is no duplication to remove today. Trigger "the order dynamic cache lands" recorded.
- None (BFS layer): single-sited in `utils/inputs.py::GeneratedInputArgumentsFactory`; this file supplies only family-hook attrs + the operator-bag-omitting `_build_input_triples` override. No fold candidate. Both correct.

### Temp test verification
- None. Pure docstring/comment reword, zero executable change — no behavior to pin (consistent with the analogous `filters/factories.py` Medium reword). No pytest run (role rule; no executable change introduced).

### GLOSSARY rot — forwarded, left untouched (independently confirmed)
- The `OrderSet` "Layer 6 deferred to `0.0.9`" pin (GLOSSARY:919) and the `Meta.orderset_class` "once it ships in `0.0.9`" pin (GLOSSARY:806) both still carry the rot — verified untouched by reading both lines. The cycle's GLOSSARY diff (`git diff 0872a20 -- docs/GLOSSARY.md`) touches ONLY lines 286 / 991 / 1001 / 1178 (closed sibling cycles: 286→rev-connection, 991/1001→rev-filters, 1178→inspect file cycle — all verified+[x]); it does NOT touch 806 or 919. So the orderset `0.0.9`-pin rot is correctly LEFT for the orders folder / project pass and recorded as forwarded in both the Summary and Worker 2's Notes. Not a local-edit-in-scope, not a reject trigger.

### Changelog disposition verification
- `Not warranted`. `git diff -- CHANGELOG.md` is EMPTY (exit 0). Disposition cites BOTH required sources: AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this cycle. Internal-only framing is honest: a docstring/comment contract-accuracy reword with zero behavior change and no consumer-visible delta; the Layer-6 surface never shipped in any release, so there is no released-contract change — correctly "Not warranted" rather than "Warranted but deferred". Accepted.

### Validation
- `uv run ruff format --check django_strawberry_framework/orders/factories.py` — 1 file already formatted (standing COM812-vs-formatter advisory only).
- `uv run ruff check django_strawberry_framework/orders/factories.py` — All checks passed.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the `orders/factories.py` checklist box in `docs/review/review-0_0_9.md`.
