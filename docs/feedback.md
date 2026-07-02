# Adversarial review — `spec-040-auth_mutations-0_0_13.md` (Revision 3)

Scope: a fresh adversarial pass on the thrice-revised spec, with every load-bearing
reuse claim re-grounded against the package source (not taken from the spec's own
prose), and cross-referenced against [`GOAL.md`](GOAL.md) and the north-star working
reference [`recipes/schema.py`](../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py).

The spec is in strong shape. Revisions 2–3 folded in the earlier findings and — verified
below — did so *correctly against the code*, not just plausibly. The findings here are
the residue those passes did not reach: two reload / composability gaps and two
contract under-specifications, plus a GOAL cross-reference.

---

## Findings

### [P2] The register-arm bind error regresses to the generic message after a reload — and the specified reload test won't catch it

**Spec anchors:** Decision 6 (lines 1236–1251, "Every factory call — cached or not —
re-registers the class into the **mutation** declaration ledger"); Decision 8 / 9
(line 1470, `bind_auth_mutations()` "validates Decision 8 for every declared
user-typed surface (`register` included, **via its auth-ledger record**)"); Edge cases
(lines 1745–1756).

**Code grounded:** `_bind_mutation` resolves the payload primary type through
`_resolve_primary_type` ([mutations/sets.py:1314](django_strawberry_framework/mutations/sets.py)),
whose no-registered-type raise is the *generic* "…which has no registered DjangoType…"
message naming the raw class. `bind_mutations()` runs *after* `bind_auth_mutations()`
per the pinned order (finalizer.py:786–788 today binds `iter_subsystem_clears()` →
`bind_mutations()`; the spec inserts `bind_auth_mutations()` between them). The whole
point of Decision 8's Revision-2 reordering is that `bind_auth_mutations()` raises the
*auth-specific* error for `register` **first**, pre-empting the generic one.

**The gap:** that pre-emption depends entirely on `register` having a live **auth-ledger**
record when `bind_auth_mutations()` runs. But the spec only ever pins the every-call
re-registration for the **mutation** ledger (line 1240). It never states when the
`register` **auth-ledger** record is written, nor that it is re-written on every factory
call. The register class is "created lazily on **first** factory call" (line 1236) and
cached — so if the auth-ledger record is written alongside that once-only synthesis
(guarded by the cache), then after `registry.clear()` drains the auth declaration ledger
(its `TypeRegistry.clear()` hand row) the record is **gone and not re-added**, while the
mutation-ledger re-register *is* re-added. Second finalize: `bind_auth_mutations()` no
longer sees `register`, skips its Decision-8 validation, and `bind_mutations()`'
`_resolve_primary_type` raises the **generic** message for a missing user type — the
exact regression Decision 8 was written to prevent, now reachable on the reload path the
autouse complete-reload fixtures exercise every test.

The specified reload test (lines 1808–1809: finalize → `registry.clear()` → re-declare →
finalize, "asserting `register` … present in the second schema") asserts *presence*, so
it passes even while the register-arm error message has silently reverted.

**Fix:** state explicitly that `register_mutation()` re-records into **both** ledgers on
every call — the mutation ledger (for binding) and the auth ledger (for Decision-8
coverage) — with the same identity-dedupe on both. **Test:** extend the reload cycle to
run the no-`UserType` case *after* a `registry.clear()` + re-declare and assert the
**register-arm auth-specific** error (distinct from the generic `_resolve_primary_type`
message) still fires on the second finalize — not merely that `register` is present when
the type does exist.

### [P2] A custom permission class receives the bare holder as its `mutation` argument — Goal 3 composability is only partly honored for `login` / `logout` / `current_user`

**Spec anchors:** Goal 3 (lines 617–623, "Compose with the existing permissions
surface… a consumer can gate any auth field… without new machinery"); Decision 5
(lines 1070–1085, the `DjangoModelPermission` incompatibility, documented "by
documentation, not a factory-time guard").

**Code grounded:** the permission holder reuses `DjangoMutation.check_permission` by
call, and that body calls
`permission_class().has_permission(info, type(self), operation, data, instance)`
([mutations/sets.py:1001–1006](django_strawberry_framework/mutations/sets.py)) — it
passes `type(self)`, i.e. the **holder class**, as the `mutation` positional. For the
model-less auth holders that object has a duck-typed `_mutation_meta` snapshot and
`_primary_type`, but **no `Meta.model`, no `_resolve_model`, none of the shape a real
`DjangoMutation` carries.**

**The gap:** the spec documents this hazard for exactly one class (`DjangoModelPermission`)
and frames it as that class's quirk. It is general: *any* consumer `has_permission` that
introspects the `mutation` argument — a DRF-style gate reading `mutation.Meta.model`, a
gate that branches on the operation by inspecting the class, etc. — breaks on the three
model-less auth fields at request time, not just the family default. Goal 3 promises
"gate any auth field without new machinery"; that holds only for gates that rely solely
on `info` / `operation` / `data` and never touch the `mutation` object.

**Fix:** broaden the Decision 5 caution from "`DjangoModelPermission` is incompatible" to
the general rule: *the `mutation` positional passed to a custom `has_permission` on
`login` / `logout` / `current_user` is an internal permission holder, not a
`DjangoMutation` — gates for these fields must key on `info` / `operation` / `data`, never
on introspecting the mutation object.* **Test:** a custom permission class reading only
`info` + `operation` authorizes/denies correctly on `login`; document (don't silently
break) that a `mutation.Meta`-reading class raises at request time — the `DenyAll`
precedent's posture, applied to the general case.

### [P3] What `data` / `instance` a `login` / `logout` permission gate receives is unspecified — undercutting the advertised rate-limit / invite gate

**Spec anchors:** line 833 ("`register_mutation(permission_classes=[InviteOnly])`"),
line 1037 ("rate-limit gate on `login`, invite gate on `register`, a locked-down
`logout`"), Decision 5 line 1057 (`authorize_or_raise(holder_cls, operation, data,
instance)`).

**Code grounded:** `authorize_or_raise(mutation_cls, info, operation, data, *, instance)`
([mutations/resolvers.py:1238–1245](django_strawberry_framework/mutations/resolvers.py))
threads `data` and `instance` straight into `check_permission` → `has_permission`.
Decision 7 pins these for `current_user` (`data=None`, `instance=<request user | None>`,
line 1312), and `register` — a real create mutation — gets the standard `data`=input.
But Decision 5 writes `authorize_or_raise(holder_cls, operation, data, instance)` for
`login` / `logout` **without ever defining `data` or `instance`.**

**The gap:** the spec advertises a per-request rate-limit gate on `login`, but a gate
that rate-limits *per account* needs the attempted `username` in `data`. If `login`
passes `data=None`, only IP-based gating (via `info.context.request`) is possible — the
per-account case the wording implies is silently unavailable.

**Fix:** pin `login`'s gate payload — recommend `data = {"username": username}` (never
the password) and `instance=None` (there is no pre-auth instance) — and `logout`'s
(`data=None`, `instance=None`). **Test:** assert a `login` gate sees the attempted
username in `data`.

### [P3] The get_queryset bypass on `login.node` / `me` is a documented deviation from GOAL success-criterion 4, and the 0.1.1-forward "FieldSet composes like any other type" claim is not obviously true for `login.node`

**Spec anchors:** Decision 5 (lines 1087–1106, login node = raw `authenticate()`
instance, no visibility, **no optimizer re-fetch**), Decision 7 (lines 1329–1335,
`current_user` runs no `get_queryset`), Out-of-scope (lines 1951–1954, field-level read
gates "will compose on top of the auth surface's returned user objects **like any other
type**").

**GOAL cross-reference:** success criterion 4 ([GOAL.md](GOAL.md) line 511) is "Enforce
row, field, and cascade permissions declaratively — **the same hook covers reads and
writes**." `me` and `login.node` deliberately bypass `get_queryset`. This is *sound* for
the actor's own row (viewing yourself is not a directory lookup, and the spec argues it
well), so it is not a leak. But it is an undocumented-as-such carve-out from a stated
success criterion, and the Revision-2 P3 caution only covers field **selection** (which
columns `UserType` exposes), not the interaction: a `UserType.get_queryset` written to
row-redact provides **no** protection on `me` / `login.node`.

**The sharper half:** the Out-of-scope line commits a future `0.1.1` FieldSet gate to
compose on the auth user objects "like any other type." Every *other* type's node is
re-fetched / optimizer-planned; `login.node` is explicitly the raw `authenticate()`
instance, per-field, **not** optimizer-planned (asymmetric with `register`'s G2-planned
re-fetch — the spec's own words, line 1098). Whether a per-field `check_<field>_permission`
fires identically on a raw, unplanned instance versus a planned node is not obvious, and
the spec asserts it without qualification for an unbuilt feature.

**Fix:** (a) add one sentence to Decision 8's caution noting that `get_queryset`
row-redaction does not apply to `me` / `login.node` (only field selection governs those
surfaces); (b) scope the Out-of-scope claim to "…returned user objects; `login.node`'s
raw-instance path will be re-examined when field gates land" rather than the unqualified
"like any other type."

---

## GOAL.md cross-reference summary

- **Cookbook / north-star parity:** the working reference
  [`recipes/schema.py`](../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py)
  (the file [GOAL.md](GOAL.md) line 3 pins as THE reference) contains **no auth surface
  at all** — it is pure read-side nodes + filter/order/aggregate/fieldset sidecars +
  `get_queryset` visibility. This confirms the spec's "single-upstream parity" framing is
  **honest**: auth is a `strawberry-graphql-django` parity item, not a cookbook-parity
  item. Consequence worth stating plainly in the spec: this card does **not** advance the
  six-file astronomy/cookbook north-star shape (GOAL "What success looks like"); it
  advances only the *fakeshop target-example* growth direction ("auth mutations exercised
  by the existing test users", [GOAL.md](GOAL.md) line 535). That is a legitimate scope —
  but the spec's framing occasionally reads as if auth is core to the north star; it is
  adjacent to it.
- **Criterion 6 (three mutation flavors, one envelope):** consistent. Auth is explicitly
  "NOT a fourth flavor," and `login`/`register`/`logout` returning `FieldError` envelopes
  upholds the Cross-subsystem invariant. No contradiction.
- **Non-goal "silently weakens rich relations into generic placeholders":** the spec
  correctly cites this (Decision 8) to reject a `JSON`/opaque user fallback. Aligned.
- **Strawberry request idiom:** the cookbook uses `info.context.user` (Graphene:
  context *is* the request); the spec correctly uses `request_from_info(info)` /
  `request.user`, matching the GOAL astronomy example's
  `info.context.request.user` shape. Correct for the Strawberry port — no finding.

---

## Verified correct (re-grounded, not taken on faith)

These Revision-2/3 claims were checked against source and hold:

- **The lifecycle split is real and correctly reasoned.** The finalizer pre-bind reset
  drains `iter_subsystem_clears()` immediately before `bind_mutations()`
  (finalizer.py:786–788); `TypeRegistry.clear()` iterates the same emit rows and *then*
  hand-rows `clear_mutation_registry` / `clear_form_mutation_registry` separately
  (registry.py:576–595), with an explicit comment that declaration-registry resets are
  **not** pre-bind input clears (registry.py:572–575). So routing the auth **declaration**
  ledger onto a `TypeRegistry.clear()` hand row (not `register_subsystem_clear`) is exactly
  right — the Revision-3 P1 fix is sound, and the earlier draft's `register_subsystem_clear`
  approach really would have drained the declarations before the auth bind read them.
- **The permission holder duck-typing is sufficient.** `check_permission` reads only
  `type(self)._mutation_meta.permission_classes` (sets.py:998); `authorize_or_raise`
  constructs `mutation_cls()` zero-arg and, on denial, does
  `getattr(mutation_cls._primary_type, "__name__", mutation_cls.__name__)`
  (resolvers.py:1264, 1276) — so a holder carrying `_mutation_meta` (with
  `.permission_classes`), `_primary_type`, and `check_permission = DjangoMutation.check_permission`
  is exactly what the reused code needs, and `_primary_type = None` for `logout` produces
  the documented holder-name fallback. Confirmed feasible.
- **Payload materialization + lazy-ref resolution.** `build_payload_type` builds both
  shapes (inputs.py:603–616) but only *creates* the class; it is
  `materialize_mutation_input_class` that parks it as a resolvable module global of
  `mutations.inputs` (inputs.py:133–147) and enforces the distinct-shape collision raise.
  So `bind_auth_mutations()` must call *both* (build then materialize) — the spec's "rides
  the existing `mutations.inputs` emit ledger" is correct, though its shorthand
  "`build_payload_type` materializes" is imprecise. The parked-globals overwrite-in-place
  lifecycle (inputs.py:155–161) means the reload path re-materializes fresh payloads with
  no staleness — so the cached `Register` rider does **not** carry a stale payload across
  reloads (a hazard I checked for and cleared).
- **The password never reaches a model column** is enforceable exactly as specced: the
  register `decode_step` returning `(user, m2m, exclude, raw_password)` and popping
  `password` before `model(**scalar_and_fk_attrs)` mirrors `_model_decode_step`'s real
  shape, and `run_write_pipeline_sync` passes only the decode return into `write_step`.

## Process note

The spec's DoD item 1 still gates on
`scripts/check_spec_glossary.py … reports OK: <N> terms` — not run here (design-only
spec; the CSV companion is a Slice-0 artifact). Flagging so it isn't assumed green.
