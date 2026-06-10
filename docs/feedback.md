# Review — spec-031 GlobalID encoding, implementation pass (`django_strawberry_framework/` only)

Rigorous code review of the shipped implementation. Scope: package source only
(tests / examples / docs deliberately not reviewed in this pass). Every claim
below was verified against the working tree; the P1 was **reproduced with a
runnable script** against the fakeshop models, not inferred from reading.

## Verified sound (checked and confirmed — not in dispute)

The implementation tracks the spec's hardest contracts faithfully:

- **Re-entrancy guard** (`types/relay.py::install_globalid_typename_resolver`
  step 0) — skips when `definition.effective_globalid_strategy` is already set,
  exactly the spec-031 Decision 10 step-0 contract; the finalizer comment at
  `types/finalizer.py::finalize_django_types #"a Phase-2.5 raise here is recoverable"`
  documents the pairing with the audit raise.
- **Recorded field** — `DjangoTypeDefinition.effective_globalid_strategy: str | None = None`
  appended among the defaulted dataclass fields, distinct from the raw
  `globalid_strategy` slot, with the invariants docstring updated. Decode and
  the strategy-aware filter both read the recorded field, never
  `_resolve_globalid_strategy` — the durable-contract cleanup landed.
- **One validator, two sources** — `types/base.py::_validate_globalid_strategy`
  serves both `Meta` and the `RELAY_GLOBALID_STRATEGY` setting with
  source-specific error text; the setting path validates callables too.
  `_is_async_globalid_callable` seeing through callable instances with
  `async def __call__` AND `functools.partial` wrappers (with the
  provably-depth-1 `.func` argument) is more thorough than the spec required.
- **`decode_global_id`** — runtime input-type gate, `relay.GlobalID.from_id`
  for the `str` branch with the `ValueError`-superset catch, empty
  `type_name`/`node_id` rejection, resolve-then-enforce with the recorded
  strategy, absent-(`None`)-strategy rejection, and `callable`/`custom`
  encode-only enforcement. Every failure path is `ConfigurationError`.
- **`registry.definition_for_graphql_name`** — Relay-Node-only scan keyed on
  `graphql_type_name` (honors `Meta.name`), unique-match contract with miss and
  ambiguity errors.
- **Model-label-routing audit** — scoped to the once-materialized
  `models_with_multiple_types()` tuple shared with the Phase-1 ambiguity audit,
  placed after the install loop and before Phase 3, with a grep-stable
  formatter. The shared-tuple optimization is a nice touch beyond the spec.
- **Strategy-aware filter** (`filters/base.py::_accepted_globalid_type_names`)
  — keyed on the recorded strategy, model-label/type-name/both acceptance,
  node-id-only fallback for `callable`/`custom`/unbound/absent; filter stays on
  `GraphQLError` (request-time surface) while decode owns `ConfigurationError`.
  `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` single-sourced in
  `types/relay.py` and imported — no re-typed membership literals.
- **AGENTS.md hygiene held elsewhere**: no new public exports
  (`__init__.py` untouched, `__version__` still `0.0.8` per the joint-cut
  boundary), `conf.py` stays a thin reader, the settings key landed with the
  feature, in-function imports carry cycle-dodge justifications, Meta-first
  consumer surface preserved (zero decorators on consumer-facing classes).

The findings below are the residual gaps.

---

## P1 — Inherited framework closure misclassifies concrete Relay subclasses (reproduced)

`types/relay.py::_consumer_overrode_resolve_typename` answers "did the consumer
override `resolve_typename`?" with the MRO-aware `__func__` identity test
against `relay.Node.resolve_typename`. The step-0 re-entrancy guard protects
the *same definition* across finalize re-runs — but it cannot protect a
**different definition that inherits the installed closure through the MRO**.

A concrete Relay `DjangoType` subclassing another concrete Relay `DjangoType`
is a supported shape (it is the natural way to write a `Meta.primary`
secondary that shares `get_queryset` / resolver overrides with the primary).
The finalizer processes registration order: the parent gets the framework
closure installed into its `__dict__`; the child is processed next, `getattr`
walks the MRO, finds the parent's closure, its `__func__` is not
`relay.Node.resolve_typename.__func__` — and the child is classified a
consumer override.

**Reproduced** (fakeshop `Item`, script run against the working tree):

```python
class ItemNode(DjangoType):           # Meta: model=Item, interfaces=(relay.Node,), primary=True
    ...
class AdminItemNode(ItemNode):        # Meta: model=Item, interfaces=(relay.Node,)
    ...
finalize_django_types()
# parent effective: model
# child  effective: custom            <- misclassified; consumer wrote no override
# child has own resolve_typename: False

class TypedChild(ItemNode2):          # Meta: ... globalid_strategy = "type+model"
    ...
finalize_django_types()
# ConfigurationError: TypedChild: declares both a resolve_typename override and
# an explicit Meta.globalid_strategy ...   <- SPURIOUS; no override exists
```

Four consequences, in decreasing severity:

1. **A valid consumer program hard-fails at finalize.** A subclass declaring a
   legitimate `Meta.globalid_strategy` trips the both-declared
   `ConfigurationError` for a `resolve_typename` override the consumer never
   wrote. The error message is unactionable — there is nothing to remove.
2. **Silent `custom` misclassification.** The child is encode-only for decode
   and the filter falls back to node-id-only — the strategy-aware guarantees
   quietly disappear for that type.
3. **The model-label-routing audit goes blind.** The audit reads recorded
   strategies; a child that *actually emits* model-label IDs through the
   inherited closure is recorded `custom`, so `_emits_model_label` reports
   False and the invariant check can pass configurations it should reject.
4. **The inherited closure captured the parent's `definition`.** Even when the
   emission is coincidentally right (same model → same label), the closure is
   the wrong object: a child whose own strategy resolves to `type` still emits
   the parent's model-label payload because nothing shadows the inherited
   closure (`type` installs nothing by design).

**Root fix (recommended — no surface patch):** make the framework closure
self-identifying and key the override test on it.

- In `_install_typename_closure`, stamp the function before wrapping:
  `resolve_typename._dsf_globalid_framework_closure = True` (the attribute
  survives `classmethod.__func__` retrieval).
- `_consumer_overrode_resolve_typename` returns False when
  `getattr(existing_func, "_dsf_globalid_framework_closure", False)` — a
  framework closure inherited from a parent is *not* a consumer override.
- The child then resolves its **own** strategy and must install its **own**
  closure in its own `__dict__` — including for the `type` classification
  whenever the inherited attribute is a framework closure (otherwise the
  parent's closure keeps shadowing Strawberry's default). This is the one case
  where `encode_typename`'s currently-dead `type` branch becomes live
  production code (see the P3 below — this fix retires that finding too).
- A consumer override inherited from an abstract base keeps working: it lacks
  the marker, so it still classifies `custom` — the intended semantics.

Add package tests for: concrete-child-of-concrete-parent classification per
strategy; the `TypedChild` spurious-error case (must finalize cleanly and
record `type+model`); a `type`-strategy child under a `model` parent emitting
the GraphQL type name (the shadowing case); and the audit seeing the child's
true recorded strategy. A live fakeshop variant belongs in `test_query/` if a
multi-type Relay pair exists there; otherwise package tests are the right
fallback per AGENTS test-placement.

Severity note: this also interacts with a plain-function or `staticmethod`
consumer override (no `__func__` → currently classified "no override" and
silently clobbered). Such an override is already broken under Strawberry's
classmethod call shape, so it is not independently P1 — but the marker-based
test makes the discrimination explicit rather than accidental; worth one
defensive test.

---

## P2 — Raw `L<NN>` line-number references in code comments (AGENTS.md source-ref rule)

AGENTS.md is explicit: raw `path:NN` line references are allowed **only** in
per-cycle scratchpad artifacts and "must not appear in code comments." The
spec-031 work *rewrote* the GlobalID filter docstrings and carried the old
spec-027 line refs forward into the new text:

- `filters/base.py::_target_definition_for` — "per spec-027 L566-567 + L603 +
  L1057", "per spec-027 L988" (new function, new docstring).
- `filters/base.py::_decode_and_validate_global_id` — "per spec-027 L602",
  "(spec-027 L603)", "per spec-027 L605" (rewritten docstring).

These are doubly rotten: the refs are line numbers, and spec-027 now lives at
`docs/SPECS/spec-027-filters-0_0_8.md` where those line positions have long
since drifted. Fix by replacing each with the symbol-qualified form the rule
prescribes, e.g. `docs/SPECS/spec-027-filters-0_0_8.md #"unique substring"`,
or by citing spec-031 Decision 13 (which now owns this behavior) where that is
the truer source.

Pre-existing instances in untouched code (`filters/sets.py` L566-567/L607/
L518-605 refs, `filters/__init__.py` "L7 of rev5") are out of this card's
blast radius but should be queued for the same sweep — the rule names
renames/moves as exactly the rot vector that hit here.

---

## P3 — `docs/feedback.md` citations in standing code comments rot every review cycle

Ten package files cite `docs/feedback.md` in comments/docstrings (the
spec-031 files among them: `types/relay.py`, `types/base.py`,
`types/definition.py`, `types/finalizer.py`). `docs/feedback.md` is a
per-cycle artifact — it has been fully replaced four times during this card
alone, and this very review replaces it again. Every such citation now points
at content that no longer exists.

The durable citation is the spec Decision, which is already present alongside
in almost every case ("spec-031 Decision 10, `docs/feedback.md` P1"). Drop the
feedback halves in the spec-031-touched files; the spec's Revision history
preserves the full finding text, so no information is lost. (Same note applies
to the pre-existing spec-030-era citations in `optimizer/`, `connection.py`,
`list_field.py`, `orders/` — sweep candidates, not this card's obligation.)

---

## P3 — Stale TODO anchor: spec-027 Slice 1 reuse has shipped

`types/relay.py #"TODO(spec-027-filters-0_0_8 Slice 1)"` (above
`_coerce_node_id`) asks for `FilterSet`'s related-branch scoping to reuse the
sync/async visibility helpers — with pseudocode. That work shipped:
`filters/sets.py` imports `_apply_get_queryset_sync` / `_apply_get_queryset_async`
at module top and calls them in the related-branch scoping
(`filters/sets.py #"scoped = _apply_get_queryset_sync(target_type, child_base, info)"`).
AGENTS.md line 26: the anchor is "removed in the same change that ships the
slice." Remove the TODO block (pseudocode included). Pre-existing miss, but
this card edited the file heavily and is the right vehicle for the deletion.

---

## P3 — Routing-audit remediation misleads when the primary is not Relay-Node-shaped

`types/finalizer.py::_format_model_label_routing_error` always says "Set the
primary's Meta.globalid_strategy to 'model' or 'type+model'…". For a
multi-type model whose **primary is not Relay-Node-shaped** (a Relay secondary
emits model-label IDs; the plain primary's recorded strategy is `None`), that
remediation is impossible — `_validate_globalid_strategy` rejects the key on a
non-Relay type. The audit *flagging* this configuration is correct (decode
would reject via the absent-strategy guard); only the fix sentence lies.
Branch the remediation on `primary_strategy is None`: "make the primary
Relay-Node-shaped (or re-declare the primary), or move the emitting type(s) to
the 'type' strategy." Add the non-Relay-primary case to the audit tests.

---

## P3 — `encode_typename`'s `type` branch is production-dead as wired

`install_globalid_typename_resolver` never installs a closure for the `type`
classification, so `encode_typename(..., "type", ...)`'s final
`return definition.graphql_type_name` is reachable only by tests calling the
helper directly. That is permissible under the coverage rules (the line is
genuinely unreachable from a live query), but a dispatch branch that exists
only to be total is a small smell — **and the P1 root fix retires it**: once a
`type`-classified child must shadow an inherited framework closure, this
branch becomes the live implementation. Resolve this finding by implementing
the P1 fix rather than by deleting the branch.

---

## Summary

| # | Sev | Area | One-line |
| - | --- | --- | --- |
| 1 | P1 | relay/finalizer | Inherited framework closure → concrete Relay subclass misclassified `custom`; spurious both-declared error; audit blind spot; wrong captured definition. Fix: sentinel-mark the closure, treat marked as non-override, install child's own closure (incl. `type` shadowing) |
| 2 | P2 | filters | Rewritten docstrings carry raw spec-027 `L<NN>` line refs — explicit AGENTS source-ref violation; replace with `#"unique substring"` / spec-031 Decision 13 citations |
| 3 | P3 | package-wide | `docs/feedback.md` citations in standing comments rot each review cycle; keep only the spec-Decision halves |
| 4 | P3 | relay | Stale `TODO(spec-027 Slice 1)` — the promised reuse shipped in `filters/sets.py`; delete the anchor + pseudocode |
| 5 | P3 | finalizer | Routing-audit fix sentence impossible for a non-Relay primary; branch the remediation on `primary_strategy is None` |
| 6 | P3 | relay | `encode_typename` `type` branch production-dead; resolved as a side effect of the P1 fix |

P1 is the one to fix before the card closes: it is a confirmed hard failure on
a valid consumer program plus a silent decode/audit correctness gap, on
exactly the multi-type-per-model surface the spec's routing invariant exists
to protect.

## Validation

- P1 reproduced via a standalone script against fakeshop models (parent/child
  concrete Relay types; output quoted above), then the script was removed.
- `decode_global_id`, the validator, the audit, and the filter acceptance were
  traced end-to-end against the spec's Decisions 4–13; no other divergence
  found.
- No package file was modified by this review.
