# Adversarial review: spec-050 candidate after the sidecar-seal follow-up

Date: 2026-09-21

Reviewed the current implementation against `docs/spec-050-list_field_arguments-0_0_15.md`,
its rationale, `docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`, `GOAL.md`,
`START.md`, `AGENTS.md`, the live-suite rules, and the Strawberry/Django integration. The
repository was already dirty when this pass began; unrelated optimizer/kanban edits were left
untouched. Ruff and `git diff --check` pass for the touched Python and documentation paths. No
pytest run was performed, as required by the repository instructions.

## Verdict

The production corrections from the last review are present. The shared post-sidecar seal now
covers `FilterSet.apply_*` and `OrderSet.apply_*` in both connection pipelines, the async live
mount really selects `connection.py::_pipeline_async`, its schema is rebuilt per request, and
`FilterSet.apply_sync` now documents a lazy return.

Spec-050 is still not ready to close. The exact-tree Decision-22 gate and evidence-only
follow-up do not exist, and the working tree contains additional intended test/documentation
changes that are not in an identified candidate commit. The async connection evidence also
claims a mirrored malformed matrix while omitting several executable async branches.

## Verified corrections

- `examples/fakeshop/test_query/test_connection_pagination_api.py` builds a local
  `DjangoConnectionField` with a genuine `async def` consumer resolver. That is the supported
  construction shape that selects `connection.py::_pipeline_async`; the previous no-resolver
  false positive is closed.
- The async OrderSet matrix records an entry sentinel, so a passing rejection proves
  `GenreOrder.apply_async` was entered rather than the request failing on an earlier path.
- The new async FilterSet matrix supplies a real `filter:` argument, records the same sentinel,
  and has an accepted `super()` control that verifies the filtered page.
- `connection.py::_pipeline_sync` and `connection.py::_pipeline_async` route both public
  sidecars through `utils/querysets.py::_apply_sidecar_sync` / `::_apply_sidecar_async` and the
  one `_SIDECAR_RESULT_POLICY`.
- The old one-shot async schema cache was replaced by a request-scoped holder that is cleared
  in `finally`, and `FilterSet.apply_sync` now says it returns a lazy queryset.
- The stale builder claim that connection FilterSet results were still unsealed has been replaced
  by a discharged entry naming the shared helpers and both pipeline call sites.

## P1 — there is still no exact candidate gate or closure evidence

### Broken contract

Decision 22 requires one immutable candidate implementation tree, the complete default/sharded/
floor/structural/documentation gate on that exact tree, one adversarial review of the gated tree,
and an evidence-only follow-up whose parent is that candidate. Only then may the card's DONE
state be treated as closure.

### Evidence

`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` remains `Status: Candidate`, leaves
the final gate unchecked, says `No gate is recorded`, and has no closing gate table or
evidence-only follow-up. The current checkout is not an immutable candidate: `HEAD` is
`24e6b4d3`, while the prior review discussed `3c53842f`, and the working tree currently carries
additional sidecar live-test, documentation, and builder changes. Earlier suite figures cannot
certify either the current `HEAD` or those uncommitted bytes.

### Required fix

Create the intended candidate commit without absorbing unrelated dirty files. Record its exact
SHA and complete parent chain. In a clean checkout of that SHA, run and record every Decision-22
gate: default coverage at `fail_under = 100`, sharded mode, the declared supported-floor scope,
format/lint and structural checks, citations, tracked-path constants, generated documentation,
`manage.py check`, and `makemigrations --check --dry-run`. Then perform the adversarial review
against that same SHA and make a follow-up commit whose only change is the gate/evidence record
and whose parent is the gated candidate. Do not mark the card closed from the current dirty-tree
state.

## P1 — the spec's lifecycle prose can be read as completed evidence while the builder says none exists

The opening status paragraph of `docs/spec-050-list_field_arguments-0_0_15.md` says that the
candidate carries the default, sharded, floor, structural, link, citation, tracked-path, review,
and evidence-only results, and says “What follows runs against this exact tree.” The builder
record explicitly says that no gate, review, or evidence-only follow-up has run against the
candidate. Those statements cannot both be the current release record: a maintainer or release
script following the spec could treat the prose as proof that the gate already ran.

Until the gate exists, rewrite the status paragraph in requirement/future tense (for example,
“must run against this exact tree and be recorded in the follow-up”), or leave the status as
candidate but remove language that sounds like completed evidence. After the exact gate and
follow-up, replace it with the actual candidate SHA, results, and parent relationship. Keep the
builder and spec as one source of truth; do not solve this by copying old figures into either
file.

## P2 — the async connection matrix is not actually mirrored across the shared seal

### Broken claim

The live module docstring and the suite-map entry say the async matrix is mirrored from the sync
matrix and that it covers the same defect shapes. The async rows do not do that.

### Evidence

The sync `GenreOrder.apply_sync` matrix covers materialized-list and `None` type defects,
projection, an awaitable returned from the sync seam, malformed deferred-filter state, and the
shape/routing defects. The async `GenreOrder.apply_async` matrix covers evaluated, sliced,
combined, wrong-model, routing mutation, and non-awaitable returns only. It has no residual
awaitable row even though `utils/querysets.py::_apply_sidecar_async` has a distinct
“residual awaitable value” branch. The new async `GenreFilter.apply_async` matrix repeats the
same six-row omission. The spec's live test plan explicitly requires residual-async-awaitable
disposal, and the package's own sidecar contract treats that branch as different from a
non-awaitable return.

This is a supported wire path: a consumer can publish a `DjangoConnectionField` with an async
resolver, send `orderBy:` or `filter:`, and return a second awaitable from the corresponding
sidecar method. The current rows do not prove the typed wire error, disposal, or masking for that
case on the connection surface. They also do not justify the module's “mirrored” wording.

### Required fix

Add independent async live rows for at least residual awaitable, projection/materialized-list or
`None` type defects, and malformed deferred-filter state wherever the shared helper can reach
them. At minimum, the residual-awaitable row must use an awaitable whose disposal can be counted,
assert the stable `ConfigurationError` wording, `data is None`, no raw exception text, and no
second await. Mirror the FilterSet arm or narrow the module and README claims to the exact rows
actually covered. Keep the package-tier rows for exact helper mechanics, but do not present them
as live connection evidence.

## P2 — the async HTTP helper masks the original failure when request setup or execution raises

`examples/fakeshop/test_query/test_connection_pagination_api.py::_post_async_genres` assigns
`result` inside `try`, clears the schema holder in `finally`, and only then reads
`result.response`. If schema construction, URL resolution, or the request itself raises before
assignment, the helper raises `UnboundLocalError` after cleanup instead of preserving the original
failure. A broken async mount can therefore report a misleading local-variable error, hiding the
actual regression and making the new evidence harder to trust.

Move the status/payload assertions into an `else` block paired with the `try`, or initialize and
re-raise while preserving the original exception. The holder must still be cleared in `finally`.
Apply the same pattern to any sibling helper introduced for this mount.

## P3 — the new positive async FilterSet test violates the live-suite test-style contract

`test_connection_async_healthy_filter_apply_async_override_still_filters` seeds `Alpha`, `Bravo`,
and `Charlie` with a loop in the test body. The live-suite checklist in
`examples/fakeshop/test_query/README.md` explicitly requires no loop in a test body and one
case/node id per case. This is not a runtime vulnerability, but it creates a governance failure
in the exact file whose new rows are being used as release evidence.

Use explicit model creates or a named seeding helper that owns the repeated setup, then keep the
test body to one observable case and its assertions. Re-run the structural/checklist gate after
the change.

## Scope disposition

- The previous async false-positive is closed; the test-local async resolver and sentinel make
  the branch selection observable.
- The previous 25-versus-27 scope mismatch is corrected in the builder's current text.
- The previous stale “FilterSet is not sealed” builder entry is corrected; the production seal is
  present in both connection pipelines.
- The previous schema-cache and FilterSet lazy-contract findings are corrected.
- The dirty optimizer/kanban files were not treated as spec-050 fixes or reverted. The candidate
  gate must exclude them unless their owner deliberately incorporates them.

## Required disposition summary

1. Produce one clean candidate containing the intended sidecar-live and documentation changes.
2. Run and record the complete Decision-22 gate on that exact candidate.
3. Align the async connection matrices with their claims, especially residual-awaitable
   disposal, and fix the helper's exception preservation.
4. Correct the loop-style violation and rerun the structural/documentation checks.

Spec-050 remains a candidate until item 2 is recorded and the async evidence claims are truthful.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../GOAL.md
