# spec-034 Permissions — Pre-Build Review

Review target: `docs/spec-034-permissions-0_0_10.md` + its companion
`docs/spec-034-permissions-0_0_10-terms.csv`. This is a pre-build spec review:
the design, the CSV contract, and — most rigorously — every claim the spec
makes about *existing* code and docs it builds on.

## Executive verdict

**Build-ready after a small set of accuracy fixes.** The design is sound, the
upstream port is faithfully described, and the decisions are well-argued. The
findings are not design defects — they are stale citations and doc drift. Two of
them (H1, H2) would actively mislead a build agent and must be fixed before the
slices start; the rest are tightening.

I verified the upstream port against the real checkout and it is accurate on
every invariant, and 14 of the 15 codebase precedents the spec cites are TRUE.
The single false one is H1.

## Findings

### H1 — `_apply_get_queryset_sync` / `_apply_get_queryset_async` no longer exist (stale, cited 5×) — HIGH

The spec cites `types/relay.py::_apply_get_queryset_sync` / `_apply_get_queryset_async`
as the canonical sync-misuse probe and the connection seam in **five** places:
Current state (line 86), Slice 1 (line 55), Decision 10 (line 308), Decision 10
alternatives (line 316), Decision 12 (line 343), plus the `[relay]` link target
(line 604).

Those symbols were **renamed and moved** in the `0.0.9` DRY pass. The behavior
the spec relies on is real, but it now lives at
`utils/querysets.py::apply_type_visibility_sync` / `apply_type_visibility_async`
(querysets.py:93-138); `types/relay.py` only *imports* them (relay.py:43-44).
`SyncMisuseError` moved with them (now `utils/querysets.py:35`,
`class SyncMisuseError(ConfigurationError, RuntimeError)`); `types/relay.py`
re-exports it.

Why it matters: a build agent following Slice 1 ("reuse the probe shape of
`types/relay.py::_apply_get_queryset_sync`") or Decision 12 ("pipelines call
`_apply_get_queryset_sync`/`_async`") will grep for a symbol that exists nowhere
in the package and is forced to guess. This is the one citation that breaks the
spec's "written against the real repo" contract.

Fix: replace all five citations with `utils/querysets.py::apply_type_visibility_sync`
/ `apply_type_visibility_async`; repoint or add the link reference (a `[querysets]`
def alongside `[relay]`). Verify the pipeline-order claim still holds at the new
home — it does: `connection.py::_pipeline_sync/_async` (connection.py:867/892)
call `apply_type_visibility_*` first, then filter, then order, then finalize
(Decision 12's ordering claim is correct; only the symbol name is wrong).

### H2 — the "stale `TODO-ALPHA-027-0.0.10` marker" premise is itself stale — HIGH

Current state (line 90), Slice 4 (lines 66, 369), and Risks (line 478) all assert
the products schema's four commented hooks carry a **stale `TODO-ALPHA-027-0.0.10`**
id that Slice 4 must correct. They do not. The live comments in
`examples/fakeshop/apps/products/schema.py` already cite the **correct**
`TODO-ALPHA-034-0.0.10` — on all four hooks (lines 67/101/135/169) and the
commented import (line 30). The string `TODO-ALPHA-027-0.0.10` appears nowhere in
the file (the only `027` is the unrelated `DONE-027-0.0.8` filters reference in
the module docstring).

Consequences:
- The Risks bullet (line 478, first half) states a **false fact about the repo**.
- Slice 4's "uncomment + correct the four hooks" (line 369) overstates the work —
  the id correction is already done; only the uncomment remains.
- The Current state section claims to be "A true description of the repo as of
  this writing" (line 82) — this point is no longer true.

Fix: correct lines 66/90/369/478 to reflect that the markers already read `034`;
reduce Slice 4's hook work to "uncomment." Note the *other* half of the Risks
bullet IS accurate — `TODAY.md:273` does carry the stale `TODO-ALPHA-033-0.0.10`
for this card (verified), so keep that and the Slice 5 `TODAY.md` fix.

### M1 — GLOSSARY `apply_cascade_permissions` body says "FK / M2M"; the spec scopes M2M OUT — MEDIUM

The shipped glossary entry (`GLOSSARY.md:173`) describes the cascade reaching
"through FK / M2M". The spec's Decision 5, Non-goals (line 108), and Edge cases
(line 387) are emphatic that **M2M is excluded** (no single-column `column` to
intersect on) and that M2M cascade has no follow-up card. So there is a live
spec↔glossary contradiction, and the spec does not acknowledge it.

Slice 5's GLOSSARY bullet (line 458) says it will "rewrite the body" but never
names removing the M2M claim — so an agent rewriting from the spec's invariant
list might preserve or re-introduce it. Fix: add to the Slice 5 GLOSSARY bullet
an explicit "correct the body's 'FK / M2M' to forward-FK / OneToOne only; M2M is
out of scope," and add a one-line note to Risks recording the pre-existing
glossary error so it isn't mistaken for a scope change.

### M2 — CSV line 3 note describes a post-Slice-5 future as present fact — MEDIUM

`spec-034-...-terms.csv:3` (`aapply_cascade_permissions`) notes the async twin is
"async twin documented inside the same entry (one concept two execution
contexts)." It is **not** — the current `apply_cascade_permissions` glossary entry
(`GLOSSARY.md:169-183`) never mentions `aapply_cascade_permissions`; that body is
written in Slice 5. The note states a planned future as a current fact.

Structural observation worth recording: `scripts/check_spec_glossary.py` passes
clean (`OK: 43 terms`, exit 0) and **silently accepts two CSV rows pointing at one
anchor** (lines 2 and 3 → `apply_cascade_permissions`) — no dedup, no collision
warning. So this inaccuracy is invisible to tooling; it has to be caught by eye.
Fix: reword the note to present-tense-true ("async twin; shares the
`apply_cascade_permissions` entry once Slice 5 rewrites the body — no own heading
by design").

### L1 — FieldSet card-number disagreement — LOW

Decision 2 (line 212) quotes the FieldSet card as `TODO-BETA-044-0.1.1`;
`docs/TREE.md:272` records the fieldset path under `TODO-BETA-046-0.1.1`. The spec
frames `044` as a quotation of the kanban card body, but the two artifacts
disagree on the number. Reconcile against the live kanban DB (card numbers are
explicitly unstable, so this is exactly the kind of drift to pin once).

### L2 — `create_users` staff-vs-superuser docstring nuance — LOW

`examples/fakeshop/apps/products/services.py::create_users` docstring says it
creates a "superuser" per unit, but the code sets `is_staff=True` only (no
`is_superuser`). Slice 4's "staff sees everything" branch keys on `is_staff`
(correct), so this is not blocking — but the Slice 4 author should not seed a
superuser expectation. A one-line note in the Slice 4 plan ("staff branch keys on
`is_staff`; `create_users` makes `staff_<n>` staff-not-superuser") prevents a
wrong fixture assumption. (Pre-existing example discrepancy, not the spec's to
fix — just to not trip over.)

### L3 — "request-scoped because it reads info.context.user" mis-describes the mechanism — LOW

Edge cases (line 391) attributes the `cacheable = False` outcome to the hook
"reading `info.context.user`." The actual shipped rule is coarser and simpler:
**any** custom `get_queryset` flips the plan uncacheable
(`optimizer/walker.py:481-483`, `_target_has_custom_get_queryset` → `cacheable =
False`), regardless of whether it reads the request. The conclusion (cascading
hooks are uncacheable) is correct; only the stated reason is imprecise. Trivial —
reword to "a custom hook is uncacheable by the shipped rule" if touching the line.

## What I verified as solid (no action)

- **Upstream port fidelity — all six invariants MATCH** against the real
  `/Users/riordenweber/projects/django-graphene-filters/django_graphene_filters/permissions.py`:
  the `related_model` + `hasattr(field,"column")` scope test (upstream:79), the
  `Q(fk__in=...) | Q(fk__isnull=True)` shape (upstream:103-105), the `ContextVar`
  seen-set with `finally` reset and `seen.discard` per frame (upstream:16/61-68/108-111),
  `_default_manager` (upstream:96), `.using(queryset.db)` with the matching
  docstring note (upstream:52-56/96), and the unconditional target call the port
  correctly identifies as the thing it *deviates* from with the
  `has_custom_get_queryset()` gate. The "ported verbatim" claims are true.
- **Codebase precedents (14/15 TRUE):** `has_custom_get_queryset()` exists, is
  tested, and the optimizer's downgrade rides it (base.py:669-696,
  walker.py:106-119); the connection pipeline applies visibility before
  filter/order/slice with post-visibility `totalCount`; `check_<field>_permission`
  gates are `(self, request)`-shaped, active-input-only, and run after
  `get_queryset`; `cacheable=False` on custom hooks; `fields_class` is in
  `DEFERRED_META_KEYS` and `aggregate_class` is a valid nearby anchor; the
  "Per-field permission hooks" 0.0.10-vs-FieldSet-0.1.1 contradiction is real; the
  `apply_cascade_permissions` glossary entry exists with the cited example; the
  `Meta.optimizer_hints` typo guard precedent; `registry.get` primary semantics;
  the GOAL.md `(request)`-vs-`(info)` same-name-different-host showcase; the
  Multi-DB "axis 2" entry; and RelatedFilter child-branch visibility derivation
  through target `get_queryset`. (The 1 false one is H1.)
- **CSV contract:** all 43 anchors resolve to real GLOSSARY headings;
  `check_spec_glossary.py` exits 0; no coverage gaps in either direction (42
  distinct spec refs reconcile with the 43 rows via the intentional line-2/3
  anchor share); `aapply_cascade_permissions` is the intentional async name, not a
  typo.
- **Design soundness:** self-referential FK (Edge cases:380) and mutual A↔B
  (line 381) are correctly handled by the seen-set (depth-1 direct narrowing, no
  infinite recursion); the async dead-end (async target hook raises from *both*
  variants in 0.0.10) is honestly documented with recourse (Decision 10); the M2M
  no-follow-up-card gap is surfaced in Risks; nullable-FK preservation, empty
  visible set, composite-PK skip, and `fields=` accepted-and-skipped semantics are
  all enumerated.

## Net assessment

Ship the build after fixing **H1 and H2** (both would mislead an implementing
agent) and folding **M1/M2** into Slice 5's doc work. L1–L3 are one-line
tightenings. Nothing in the design needs rework — the cascade mechanism, the
sync/async contract, the composition-by-pinning posture, and the per-field-surface
deferral are all correct and well-justified.
