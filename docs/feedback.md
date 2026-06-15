# spec-034 Permissions — Staged-Seam vs Spec Audit (code TODO anchors)

Reviewed every `TODO(spec-034 Slice N)` anchor placed in the codebase against the
current spec (`docs/spec-034-permissions-0_0_10.md`, through Revision 6) and its
test plan. Each claim below was checked against the live files, not the prose.

**Verdict: the staged seam is frozen at the Revision-3 spec and has drifted from
the current contract.** It carries the Rev-3 bare-string guard but *none* of the
Revision-5 additions — and one of those (the MTI parent-link exclusion) is a
security-relevant scope change the pseudo-code now actively contradicts. Two HIGH
findings must be reconciled before Slice 1 is written; the rest are tightenings.

Fix direction is called out per finding. The spec is authoritative for H1–H3 (they
are *code*-lags-spec) — do **not** weaken the spec to match the stale code unless
you are deliberately reversing the Revision-5 decisions. L1–L2 are the only genuine
spec patches.

## Findings

### H1 — `_cascade_edges` scope test omits the MTI `parent_link` exclusion (the pseudo-code is wrong against the current spec) — HIGH — fix: CODE

`django_strawberry_framework/permissions.py:170-189` stages `_cascade_edges` with
the **two-predicate** upstream test only:

```python
#   return [
#       f
#       for f in model._meta.get_fields()
#       if getattr(f, "related_model", None) is not None and hasattr(f, "column")
#   ]
```

Revision 5 added a **third** predicate to Decision 5 step 1:
`AND NOT getattr(field.remote_field, "parent_link", False)`. The spec references
`parent_link` five times (Decision 5 step 1, the Slice 1 checklist, the Edge-cases
bullet, the test plan, and the Revision 5 entry); `permissions.py` references it
**zero** times. Verified empirically (last round) that an MTI child's
`<parent>_ptr` `OneToOneField(parent_link=True)` carries both a `related_model`
and a `column`, so the staged pseudo-code, if implemented verbatim, **walks the
MTI parent link** — silently narrowing a child row by its MTI-parent type's hook.
That is exactly the surprising, security-relevant inclusion Rev 5 excluded by
design.

This is the one anchor that would ship a Decision-5 violation if a dev implements
it as written. The docstring compounds it (see M1).

Fix (code): add the `parent_link` predicate to the `_cascade_edges` pseudo-code,
and to its docstring's exclusion list (it currently enumerates M2M / reverse /
generic / composite "by construction" and stops — MTI parent-link is *not*
excluded by construction, it needs the explicit guard).

### H2 — four Slice-1 test stubs from the current spec test plan are missing — HIGH — fix: CODE

`tests/test_permissions.py` collects 26 skip-stubs and reads as a complete plan,
but it is the Rev-3 test plan. Four tests the current spec (Rev 5) lists under
Slice 1 have **no stub** (confirmed `grep` count 0 in the file, ≥1 in the spec):

- `test_mti_parent_link_edge_excluded` — the pin that would *catch H1*. Its absence
  is why H1 can ship silently.
- `test_secondary_type_as_root_reaches_primary_on_transitive_revisit` — the
  secondary-as-root narrowing-by-primary case (Rev 5 Edge case).
- `test_cascade_target_sliced_or_values_queryset_is_consumer_bug` — the
  cascade-target return contract (`.values()` mis-narrows / multi-col `ValueError`;
  slice = MySQL-only hard error). Rev 5 Edge case.
- `test_fields_empty_list_cascades_nothing` — `fields=[]` defined no-op vs
  `fields=None`. Rev 5 Edge case.

The file does carry the Rev-3 `test_fields_bare_string_raises`, which fixes the
drift window precisely: the stub author worked from a spec snapshot **after**
Revision 3 and **before** Revision 5. A dev who treats the stub file as the Slice-1
checklist (it explicitly invites that — "shows the whole permissions test plan as
pending") will ship four invariants untested, including the one guarding H1.

Fix (code): add the four skip-stubs in their spec-ordered homes (three in the
"remaining contract" block, `test_mti_parent_link_edge_excluded` among the scope
pins).

### H3 — `permissions.py` docstrings claim the scope test is "ported verbatim" and count "two deviations" — HIGH (prose half of H1) — fix: CODE

Two docstring statements actively misdirect the implementer away from H1:

- Module docstring, `permissions.py:25-32`: *"The four upstream invariants (ported
  verbatim …): … single-column forward scope …"* and *"Two deliberate deviations
  from upstream: the registry primary lookup … and the `has_custom_get_queryset()`
  gate."* After Rev 5 the single-column scope is **not** verbatim, and there are
  **three** package tightenings (the MTI `parent_link` exclusion is the third).
- `_cascade_edges` docstring, `permissions.py:173-178`: *"The upstream scope test,
  ported verbatim"* — same overstatement at the function a dev reads right before
  implementing it.

I flag this separately from H1 because the prose is what the implementer trusts
first; leaving it as "verbatim/two deviations" all but guarantees the `parent_link`
guard gets dropped even if the pseudo-code is fixed. Fix both strings to "two
predicates ported from upstream plus one package tightening (MTI parent-link
exclusion)" and bump the deviation count to three.

### M1 — Slice-1 line-delta / test-count estimate is stale — MED — fix: SPEC

The Implementation-plan table (Slice 1 row) estimates *"~14 (walk + invariants ×4
+ `fields=` validation + `SyncMisuseError` + async variant + export pins)"*. The
current Slice-1 test plan lists **23** tests (after the Rev-3 bare-string pin and
the four Rev-5 pins). "~14" now understates the slice by a third and will skew the
build estimate. Bump to ~19–23 and, if you want the breakdown honest, add
"+ MTI / secondary-root / target-contract / empty-fields edge pins."

### L1 — spec "Current state" version parenthetical is stale — LOW — fix: SPEC

Spec intro (line 3) says *"the on-disk version is still `0.0.8` at spec-authoring
time; the `0.0.9` cut is also still pending on `033`."* `__init__.py` now reads
`__version__ = "0.0.9"` — the `0.0.9` cut has landed. This doesn't affect Decision
13 (the `0.0.10` bump is still the joint cut's job), but the spec claims to be "a
true description of the repo," so the parenthetical should read `0.0.9`. (The
`tests/base/test_init.py` version pin and the export anchor are otherwise correct —
see below.)

### L2 — `test_single_column_scope_skips_m2m_reverse_and_generic` stub under-describes — LOW — fix: CODE

`tests/test_permissions.py:48-55` says the scope test returns "exactly the two
forward single-column relations (the others … excluded **by construction**)." Once
H1 lands, that's incomplete: the MTI parent-link is excluded *by an explicit guard*,
not by construction. Either fold a one-line MTI assertion into this test or
(cleaner) rely on the new `test_mti_parent_link_edge_excluded` from H2 and adjust
this docstring's "by construction" wording.

## Verified correct (no action — and worth keeping)

These anchors match the current spec exactly; the audit confirms them rather than
flags them:

- **Package-root export seam** — `django_strawberry_framework/__init__.py:25-39`:
  exports the pair in Slice 1, with `__all__` + the `test_init.py` pin in the same
  change, cites Decision 4. The paired `tests/base/test_init.py:35` anchor adds the
  two names alphabetically and explicitly leaves the version pin untouched
  (Decision 13). Correct on both counts.
- **Signature + async twin** — `permissions.py:67-72` is
  `apply_cascade_permissions(cls, queryset, info, fields=None)` and `:167` binds
  `aapply_cascade_permissions = sync_to_async(thread_sensitive=True)(apply_cascade_permissions)`
  — matches Decision 5 / Decision 10 verbatim. The `NotImplementedError` seams are
  loud and correctly placed (both the public fn and `_cascade_edges`).
- **ContextVar + asgiref note** — `permissions.py:57-64` carries the Rev-4
  copy-context isolation reasoning in the seen-set comment. Consistent.
- **Bare-string guard** — present in both the spec (Rev 3) and the validation
  pseudo-code (`permissions.py:97-103`); the `fields=[]` no-op behavior also falls
  out of the staged validation/loop logic correctly (only its *test* is missing,
  per H2).
- **Slice 2/3/4 seam stubs match the test plan file-for-file**:
  `tests/optimizer/test_extension.py:3976,3986` (downgrade + uncacheable — and the
  3976 stub already carries the Rev-5 "narrows with the request user" framing);
  `tests/test_connection.py:1389` (edges + post-visibility `totalCount`);
  `tests/test_relay_node_field.py:1027,1032` (node/nodes null holes);
  `tests/test_list_field.py:1019` (list default resolver);
  `examples/fakeshop/test_query/test_products_api.py:740,752,763,769,779` (the five
  live pins, with the `staff_<n>` is-staff-not-superuser note from Rev-2 L2 baked
  into the `test_cascade_staff_sees_everything` docstring). All slice tags are
  correct.
- **Products activation comments** — `examples/fakeshop/apps/products/schema.py:30`
  and the four hook comments are correctly tagged Slice 4 / `TODO-ALPHA-034-0.0.10`
  (the Rev-2 H2 correction held; no stale `027`).

## Net

The architecture and the wider seam are sound; the damage is localized and has a
single root cause — **the `permissions.py` + `test_permissions.py` pair was staged
against the spec between Revision 3 and Revision 5 and never refreshed.** Close H1
(scope-test pseudo-code), H3 (its docstrings), and H2 (the four missing pins, one
of which guards H1) together, in the code, before Slice 1 starts — they are the
same drift seen from three angles. M1/L1 are two-line spec tidies; L2 follows H2.
After that, the seam is a faithful, build-ready scaffold of the current contract.
