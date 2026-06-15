# spec-034 Permissions — Implementation Review (post-build)

Reviewed the full implementation delta (`8c5fe2a7..HEAD`, the "Finish build-034"
work) against the spec contract. Every claim below was checked against the live
code and, where behavior was in question, run — not reasoned about. The source
footprint is tight and correct in shape: the only non-test source changes are
`django_strawberry_framework/permissions.py` (the cascade) and `__init__.py`
(exports); Slices 2–3 correctly added **no** source in `optimizer/` /
`connection.py` / `relay.py` / `list_field.py` (they are pins, as specced); Slice
4 activated the four products hooks.

**Verdict: the implementation is correct and, in three places, *more correct than
the spec* — it caught a latent Django-6.0 scope-leak the spec (and my own prior
review passes) missed.** No implementation bug found. The actionable items are a
spec patch the code already proves out (H1), one test that passes for the wrong
reason and can't verify its own claim (M1), and two low spec/test tidies. The fix
direction for H1/L1 is the **spec**, not the code.

## Findings

### H1 — The spec's `hasattr(field, "column")` scope test is a Django-6.0 scope-leak; the implementation correctly uses `getattr(..., None) is not None` — HIGH — fix: SPEC

`permissions.py::_is_cascadable_edge` (permissions.py:102-106) tests:

```python
getattr(field, "related_model", None) is not None
and getattr(field, "column", None) is not None
and not getattr(field.remote_field, "parent_link", False)
```

The spec — Decision 5 step 1, the Slice 1 checklist, the `_cascade_edges`
docstring, and my own Revision-5 edits — all specify the middle predicate as
`hasattr(field, "column")` and call it "the upstream test, ported verbatim."
**That formulation is wrong under Django 6.0 and the implementation is right.**
Verified empirically against the live models:

| field | type | `hasattr(f,"column")` | `getattr(f,"column",None)` |
| --- | --- | --- | --- |
| `Book.genres` | `ManyToManyField` | **True** | **`None`** |
| `Branch.tags` | `GenericRelation` | **True** | **`None`** |

So `hasattr` is `True` for M2M and `GenericRelation` (their `column` attribute
exists and is `None`). The spec's test would therefore **walk M2M and
`GenericRelation` edges**, composing `Q(genres__in=<subquery>)` — an M2M join that
fans out duplicate parent rows and applies wrong-shape visibility — on a
security-relevant row-visibility surface. The implementation's
`getattr(field, "column", None) is not None` excludes them (column is `None`), and
the module docstring (permissions.py:86-100) documents exactly this reasoning.

This is the most important outcome of the review: the "ported verbatim" invariant
the spec leaned on is a latent bug at the project's actual Django version, and the
build correctly deviated to fix it. **Patch the spec** — Decision 5 step 1, the
Slice 1 checklist scope test, and the Revision-5 edge-case wording — to the
`getattr(..., None) is not None` form, and stop calling the `column` predicate
"verbatim" (it is a required Django-6.0 correction, alongside the `parent_link`
tightening). Consider a one-line note that `hasattr` is insufficient here.

### M1 — `test_cascade_view_item_user_matrix` passes for a different reason than its docstring claims, and cannot verify the per-edge behavior it asserts — MEDIUM — fix: TEST

`examples/fakeshop/test_query/test_products_api.py::test_cascade_view_item_user_matrix`
docstring: *"the entry-level cascade reaches the hidden Category through `item`."*
That is mechanically false given the implemented hooks. Trace, with the seeder
`_seed_cascade_split` (which gives `entry_under_private` **both** `item=item_under_private`
*and* `property=priv_prop`, **both** under the private category):

- The `view_item` user hits `ItemType.get_queryset`'s `view_item` branch →
  `queryset.filter(is_private=False)` (schema.py:105-106) — **no cascade**. So
  `item_under_private` is visible (the test asserts this), and the Entry→`item`
  edge resolves to a set that *includes* it. The item edge therefore **cannot drop
  the entry**.
- The entry actually drops via the **`property` edge**: the user has no
  `view_property`, so `PropertyType.get_queryset` cascades into `CategoryType`,
  which hides `private_cat`, so `priv_prop` is not visible →
  `Q(property__in=visible) | Q(property__isnull=True)` excludes the entry.

So the test passes, but **through `property`, not `item`** — and because both edges
of the private entry point at the private category, the test *cannot distinguish*
the two paths. It does not actually verify the "through item" composition it
documents, and it masks the real (and per-spec-correct) semantics: the
`view_<model>` branch sees all non-private rows of its own type with **no
cascade**, so the `item → category` cascade is short-circuited for a `view_item`
user. Confirmed by running it (passes) plus the source trace.

Recommend: (a) correct the docstring to "through `property`"; and (b) add an
isolating fixture — an entry whose `item` is under the private category but whose
`property` is `NULL` or under a public category — and assert it **survives** for
the `view_item` user. That pins the genuine per-edge contract (Slice 4: "a
`view_<model>` user sees all non-private rows") instead of implying a cascade that
the implementation, correctly, does not run.

### L1 — Spec pseudo-code uses `cls.model`, which does not exist — LOW — fix: SPEC

The implementation reads the model via `cls.__django_strawberry_definition__.model`
(permissions.py:181). The spec's Decision 5 pseudo-code / staged stub used
`cls.model` (e.g. `_cascade_edges(cls.model)`). Verified: `EntryType.model` raises
`AttributeError` — `DjangoType` exposes no `.model`; the canonical accessor is the
definition object. A dev following the spec's pseudo-code literally would crash on
the first line. Align the spec's pseudo-code to
`cls.__django_strawberry_definition__.model`.

### L2 — `fields=` validation runs on every (including re-entrant) call — LOW — fix: none (already specced) 

`_validate_fields` is invoked before the cycle-guard install on every call, so a
transitive/cyclic cascade re-validates `fields=` per frame. This is the exact
redundancy Decision 9's Revision-5 note already records as "redundant-but-bounded,
absorbed by the memo fallback." Noting only to confirm it's intentional and
matches the spec — no change wanted.

## Verified correct (no action)

Each checked against the spec Decision it implements; all confirmed:

- **Cycle guard (Decision 5 step 5).** Root installs `seen={cls}` and resets the
  `ContextVar` in `finally`; re-entry on a seen class returns the queryset
  unchanged (partial-narrow, never raises); each non-root frame `discard`s its own
  class so sibling edges re-visit. Validation runs *before* the install, so a bad
  `fields=` cannot leak a stale seen-set. `test_cycle_guard_*` and
  `test_self_referential_fk_cascades_once` pass.
- **Decision 8 alias pinning** — `field.related_model._default_manager.using(queryset.db).all()`:
  the resolved-alias property, `_default_manager` not `.objects`. Correct.
- **Decision 5 Q-shape** — `Q(<edge>__in=target_qs) | Q(<edge>__isnull=True)`:
  nullable-FK preservation intact.
- **`has_custom_get_queryset()` gate + registry primary lookup** — identity-hook
  targets skipped (no dead `__in`); targets resolved via `registry.get` (primary).
- **Decision 10 sync/async** — one sync-misuse site: the per-edge probe is
  `utils/querysets.py::apply_type_visibility_sync` (no re-spelled coroutine check),
  and the async twin is `sync_to_async(thread_sensitive=True)` over the *same* sync
  walk. An `async def` target hook raises `SyncMisuseError` from both. Matches the
  contract exactly.
- **MTI `parent_link` exclusion** (Rev 5) and **bare-string guard** + **`fields=[]`
  no-op** (Rev 3 / Rev 5) — all present and pinned (`test_mti_parent_link_edge_excluded`,
  `test_fields_bare_string_raises`, the empty-iterable path).
- **Exports (Decision 4 / DoD 5 / Decision 13)** — `__init__.py` imports both
  symbols and adds them to `__all__` (alphabetical); `tests/base/test_init.py` pin
  grew to match; the version pin is untouched.
- **Slices 2–3 are pins** — zero source changes in `optimizer/walker.py`,
  `connection.py`, `relay.py`, `list_field.py`; the composition tests live in the
  existing suites (`test_extension.py`, `test_connection.py`,
  `test_relay_node_field.py`, `test_list_field.py`).
- **Slice 4 activation** — the four hooks match the literal Slice 4 contract
  (staff → all; `view_<model>` → non-private; else → `filter(is_private=False)` +
  cascade). (The only semantic subtlety is M1, which is a test-accuracy issue, not
  a hook bug.)

## Verification run

- `permissions.py` coverage: **100%** (59/59 statements) from the permissions +
  products suites.
- Targeted run: **36 passed, 1 skipped**. The single skip is
  `test_multi_db_subquery_pinned_to_caller_alias`, correctly
  `@pytest.mark.skipif(FAKESHOP_SHARDED != "1")` and built on the
  `tests/optimizer/test_multi_db.py` pattern, exactly as the spec's Slice-1 harness
  note prescribed — not an unfinished stub.
- Full `fail_under=100` gate: **passed** — `1948 passed, 4 skipped`, **TOTAL
  coverage 100.00%** ("Required test coverage of 100.0% reached"), exit 0. The 4
  skips are environment-gated (`FAKESHOP_SHARDED`), not unfinished work.

## Net

No implementation defect. The build is faithful to the spec and, on the `column`
scope test (H1), the `cls.model` accessor (L1), and the MTI guard (already folded
in), it is *more* correct than the written contract — so the residual work is to
**patch the spec to match the code** (H1, L1), not the reverse, plus one test
(M1) that should isolate the per-edge path it claims to test. Ship after those.
