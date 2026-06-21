# Review: `django_strawberry_framework/relay.py`

Status: verified

DRIFT RE-REVIEW. The package-root `relay.py` (root Relay refetch fields
`DjangoNodeField` / `DjangoNodesField`) was verified earlier in cycle 0.0.11;
commit `7a17ba75` ("Promote model_for(type_cls) to utils") changed it (+4/-3)
afterward, re-opening this item. Re-reviewed against CURRENT (HEAD) source.

This-cycle scope is empty: both `git diff a7319d2f4edc7e6c1e96be04571d71e13611e3dc -- django_strawberry_framework/relay.py`
AND `git diff HEAD -- django_strawberry_framework/relay.py` are EMPTY — the
`7a17ba75` change is cumulative-in-HEAD, not a pending edit. The change is a
pure semantics-identical read-site delegation (see below). No High, no
behaviour-changing Medium, no GLOSSARY drift, every Low forward-looking →
**no-source-edit cycle (shape #5)**.

## DRY analysis

- None — the `7a17ba75` change IS a DRY consolidation that landed: the read-sites
  that reached into `types/relay.py::_model_for` (a private symbol imported across
  a module boundary) plus the raw `__django_strawberry_definition__.model` reads
  in `permissions.py`, `connection.py`, and `mutations/resolvers.py` (3 sites)
  were all promoted to the single `utils/querysets.py::model_for(type_cls)` source
  of truth, and `types/relay.py` dropped the private `_model_for`. In `relay.py`
  the two read-sites (`_coerce_pk_or_none` #"model = model_for(resolved_type)" and
  `decode_model_global_id` #"model_for(resolved_type) is not expected_model") now
  both call the shared helper. `grep -rn "_model_for"` returns zero hits — no
  orphaned twin remains. No further file-local consolidation candidate exists; the
  decode + model-check + pk-coercion contract is already single-sourced through
  `decode_model_global_id` (spec-036 DRY-2), consumed by `mutations/resolvers.py`
  (root `id:` + relation `<field>_id` decode).

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_validate_node_target` (`relay.py:228-245`)
  is a thin wrapper over the 0.0.9 shared
  `list_field.py::_validate_relay_djangotype_target` (shared with
  `connection.py::DjangoConnectionField`). `_decode_or_graphql_error`
  (`relay.py:78-99`) wraps the single decode source
  `types/relay.py::decode_global_id`. `_coerce_pk_or_none` (`relay.py:102-153`)
  is the one pk coercer reused by `decode_model_global_id` so an uncoercible
  literal never reaches the ORM as a raw `ValueError` (feedback CR-1). As of
  `7a17ba75` the model handle lookup is the shared `utils/querysets.py::model_for`
  (`relay.py:139`, `relay.py:220`), which returns
  `type_cls.__django_strawberry_definition__.model` verbatim
  (`utils/querysets.py:105`) — and `initial_queryset` itself now seeds from the
  same helper (`utils/querysets.py:118`).
- **New helpers considered.** None warranted this cycle — the change under
  review is itself the promotion of a model-lookup helper. `_interleave`,
  `_check_nodes_result`, `_stamp_node_type`, `_await_and_stamp` each serve a
  distinct single concern; no further extraction improves readability.
- **Duplication risk in the current file.** The two repeated literals flagged
  by the static helper (`"DjangoNodeField"` ×3, `"DjangoNodesField"` ×3) are
  the factory-name debug entries appended to `_node_fields_declared` plus the
  `field=` self-naming arg — intentional self-identification, not consolidatable
  duplication.

### Other positives

- **`model_for` promotion preserves semantics exactly.** `model_for` returns
  `type_cls.__django_strawberry_definition__.model` verbatim, so the two swapped
  call sites are byte-for-byte behaviour-identical to the prior `_model_for`
  reads. The model handle is used only for the `_meta.pk` / `_meta.get_field`
  coercion-field lookup (`_coerce_pk_or_none`) and the model-identity check
  (`decode_model_global_id` #"is not expected_model") — it is **never**
  substituted for the visibility queryset seed. The visibility path stays
  `resolve_node(s)` → `get_queryset` (`relay.py:373`, `relay.py:462`,
  `relay.py:477`), so the no-existence-leak property and refetch dispatch are
  unchanged. No leak/refetch regression.
- **Import direction stays acyclic / cycle-safe.** The import moved from
  `.types.relay import ..._model_for...` to `.utils.querysets import model_for`
  (`relay.py:66`). `utils/querysets.py`'s docstring explicitly allows
  `types/relay.py` to import from it, and `relay.py` (package root) importing a
  `utils/` leaf is a forward edge — no cycle introduced.
- **Error-family separation intact.** `GLOBALID_INVALID` is raised only for
  malformed/undecodable ids via `_decode_or_graphql_error` (narrow scope: wraps
  the decode call only, so `SyncMisuseError` surfaces as itself); hidden /
  missing / uncoercible-pk ids resolve to `null` with no query issued. The
  `model_for` swap touches neither boundary.
- **GLOSSARY accurate, no drift.** `#djangonodefield` (`docs/GLOSSARY.md:400`)
  and `#djangonodesfield` (`:408`) describe the public contract — null for
  hidden/missing (shared queryset path, no existence leak), `GLOBALID_INVALID`
  for malformed, per-type batched + order-preserving, honors `get_queryset`,
  typed-form wrong-type `GraphQLError` — and match the current source.
  `model_for` is a private `utils` helper (no `__all__`, no GLOSSARY entry);
  absence is correct and the contract-level GLOSSARY prose abstracts over the
  internal lookup, so the promotion causes zero drift.

### Summary

A drift re-review of the package-root `relay.py` after commit `7a17ba75`. The
sole change is a semantics-identical delegation of the model-handle lookup to
the freshly-promoted `utils/querysets.py::model_for` at two read-sites, plus the
matching import swap; `model_for` returns the same
`__django_strawberry_definition__.model` attribute verbatim and is used only for
the coercion-field / model-identity reads, never the visibility queryset seed —
so the no-existence-leak and refetch behaviour are unchanged. Both the baseline
and HEAD diffs for this file are empty (work cumulative-in-HEAD), no
public-symbol GLOSSARY drift, no High / Medium / Low. Genuine shape #5
(no-source-edit cycle).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (289 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
- This-cycle diff is empty: both `git diff a7319d2f4edc7e6c1e96be04571d71e13611e3dc -- django_strawberry_framework/relay.py`
  and `git diff HEAD -- django_strawberry_framework/relay.py` return nothing —
  the `7a17ba75` `model_for` promotion is cumulative-in-HEAD.
- `model_for` (`utils/querysets.py:94-105`) returns
  `type_cls.__django_strawberry_definition__.model` verbatim; the two swapped
  call sites (`relay.py:139`, `relay.py:220`) are behaviour-identical to the
  prior `_model_for` reads. Verify the quoted substrings, not the line numbers.
- Semantics preservation verified: model handle used only for coercion-field /
  model-identity reads, never the visibility queryset seed → no existence-leak /
  refetch regression.
- `grep -rn "_model_for" django_strawberry_framework/` returns zero — the
  private twin is fully removed; no orphan remains.
- No GLOSSARY-only fix in scope: `#djangonodefield` / `#djangonodesfield` are
  accurate; `model_for` is a private helper with no GLOSSARY entry (absence
  correct).
- Per-Low disposition: no Lows raised.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No source edits, so no
comment/docstring changes. The module/function docstrings remain accurate post
`model_for` promotion — `_coerce_pk_or_none` and `decode_model_global_id` both
describe coercing through the resolved type's id field and the model-identity
check without naming the now-promoted helper, so no docstring references the old
`_model_for` symbol.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source
edit this cycle (semantics-identical delegation already in HEAD; AGENTS.md "Do
not update CHANGELOG.md unless explicitly instructed", and the active plan
`docs/review/review-0_0_11.md` records no changelog requirement for this item).

---

## Verification (Worker 3)

Drift re-verification of the package-root `relay.py` after commit `7a17ba75`
(`model_for(type_cls)` promotion to `utils/querysets.py`). Shape #5
no-source-edit cycle.

### Stability / zero-edit proof
- `git diff HEAD -- django_strawberry_framework/relay.py` — EMPTY (no pending
  edit; no further drift this cycle).
- `git diff a7319d2f4edc7e6c1e96be04571d71e13611e3dc -- django_strawberry_framework/relay.py`
  — EMPTY (the `7a17ba75` change is cumulative-in-HEAD, not pending).
- `relay.py` ABSENT from the owned-paths `--stat`
  (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) vs
  baseline — no hunk to attribute. Shape-#5 zero-edit proof holds.
- Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle
  pattern." (#5 gate satisfied).

### Logic verification outcome (model_for promotion semantics)
No High / Medium / Low raised; independently confirmed the promotion is
semantics-identical and leak-safe:
- **`model_for` returns the attr verbatim.** `utils/querysets.py::model_for`
  #"return type_cls.__django_strawberry_definition__.model" — byte-for-byte the
  prior `_model_for` read. The two swapped sites are behaviour-identical.
- **Exactly two read-sites, both narrow.** `grep -n "model_for" relay.py` →
  import (`:66`) + `_coerce_pk_or_none` #"model = model_for(resolved_type)"
  (handle used ONLY for `_meta.pk` / `_meta.get_field(id_attr)` coercion-field
  lookup) + `decode_model_global_id` #"model_for(resolved_type) is not
  expected_model" (model-identity check only). The handle is NEVER substituted
  for the visibility queryset seed.
- **No existence-leak / refetch regression.** The visibility path stays
  `resolve_node(s)` → `get_queryset` — confirmed the defaults
  (`types/relay.py::_resolve_node_default` #"get_queryset-aware",
  `_resolve_nodes_default`, async siblings, and `_NODE_DESCRIPTORS` registering
  `("resolve_node", ...)` / `("resolve_nodes", ...)`) seed from `get_queryset`,
  independent of any `model_for` handle. The bare `node`/`nodes` resolvers in
  `relay.py` (`:373`, `:462`, `:477`) call `resolved.resolve_node(s)`, never the
  model handle, for row fetch. No leak/refetch regression.
- **Old private twin fully removed.** `grep -rn "_model_for"
  django_strawberry_framework/` → ZERO hits. No orphan straggler.

### DRY findings disposition
DRY-None accepted. The `7a17ba75` change IS the DRY consolidation landing —
`grep "_model_for"` zero-hits confirms no twin survives; the decode +
model-check + pk-coercion contract stays single-sourced through
`decode_model_global_id` (spec-036 DRY-2). No further file-local extraction
candidate.

### GLOSSARY accuracy (#4-vs-#5 gate)
- `#djangonodefield` (`docs/GLOSSARY.md:400`) and `#djangonodesfield` (`:412`)
  describe the public contract verbatim against source — null for
  hidden/missing/uncoercible (shared `get_queryset` path, no existence leak),
  `GLOBALID_INVALID` `GraphQLError` for malformed, typed-form wrong-type
  `GraphQLError`, per-type batched + order-preserving, honors `get_queryset`.
  CORRECT vs live source, not merely untouched.
- `model_for` is a private `utils` helper: `querysets.py` has no `__all__`,
  `grep "model_for" docs/GLOSSARY.md` → zero hits. Absence is correct (private
  symbol carries no GLOSSARY entry); contract-level prose abstracts over the
  internal lookup → zero drift. Not a disqualifying GLOSSARY-only fix.

### Temp test verification
- None used — empty diff, claims verified by grepping quoted substrings against
  live source per #27 content-not-identifier.
- `tests/test_relay_node_field.py` present (34 `test_` cases) covers the refetch
  contract; no new test required for a semantics-identical delegation.

### Changelog disposition
`Not warranted` — verified `git diff -- CHANGELOG.md` EMPTY; disposition cites
BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND
the active plan's silence. Internal-only framing matches the (empty) diff scope.
Accepted.

### Validation
- `uv run ruff format --check django_strawberry_framework/relay.py` — 1 file
  already formatted.
- `uv run ruff check django_strawberry_framework/relay.py` — All checks passed.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
re-opened `relay.py` checkbox in `docs/review/review-0_0_11.md`.
