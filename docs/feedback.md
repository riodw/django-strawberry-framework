# Adversarial Implementation Review: Spec-050 (`list_field_arguments-0_0_15`)

**Verdict: NOT ACCEPTED.** The implementation is not ready to certify. The review covers the
current `HEAD` (`648214b4`), the production code it contains, the complete
[Spec-050][spec-050], the [build record][build-050], and the repository rules in
[AGENTS.md][agents] and [GOAL.md][goal]. I used static inspection and live `uv run python`
probes against the fakeshop database; no pytest run was performed because the repository rules
prohibit running it after edits unless explicitly requested.

The most serious defect is not in the query compiler seal: it is in the supposedly universal raw
list bounding seam. A consumer can return a sequence object whose slice operation ignores the
requested window, and the package returns every row. Two independent policy-authority problems
remain as well. They invalidate the spec's claims that the budget is unreachable from resolver
code and that one immutable policy is used throughout an operation.

## P1-1 — A materialized sequence subclass can return an unbounded page

Spec-050 Decision 8 promises that materialized sequences receive the same `[start:stop]` window
as a queryset, and `resource_policy.py::bounded_rows` documents an unconditional raw-list bound.
The implementation does not enforce that contract. `resource_policy.py::_windowed_rows` dispatches
directly to `result[:limit]` or `result[start:stop]` and only falls back for `TypeError` and
`KeyError`. Python permits a `list` or `tuple` subclass to override `__getitem__`, including for
slice objects, so the operation being used as the security boundary is consumer-controlled.

This is reachable through the public `DjangoListField` materialized-source path, not merely a
private helper. The following real schema probe used a `DjangoSchema`, a registered fakeshop
`BranchType`, and `ResourcePolicy(max_list_rows=2)`:

```python
class Escape(list):
    def __getitem__(self, key):
        if isinstance(key, slice):
            return list(self)          # ignores the requested limit
        return super().__getitem__(key)

def resolver(root, info):
    return Escape(Branch.objects.all())
```

Executing `{ branches { id } }` returned all 23 database rows with no GraphQL error, despite the
policy being two rows. The same defect is present for the offset window and for `limit: 0`:
`result[start:start]` still dispatches the hostile slice and can return data where the contract
requires an empty result. A tuple subclass has the same behavior. This bypasses both the response
row ceiling and the amount of data a caller can make the GraphQL executor serialize.

**Root-cause correction:** make the bounding seam operate only on framework-owned sequence
representations. Either reject sequence subclasses before slicing or use exact built-in
operations (`list.__getitem__` / `tuple.__getitem__`) and verify the returned representation and
length before it leaves the seam. Do not treat a successful arbitrary `__getitem__` call as proof
that a bound was applied, and do not solve this with a post-hoc test-only length assertion that
itself calls a hostile `__len__`. The same policy must cover the zero-window branch and both
sync/async colors. Add package tests for hostile list/tuple/mapping slicing and a live
`examples/fakeshop/test_query/` test using a materialized subclass; that is a public path under
the live-test rule in [test-query README][live-readme].

## P1-2 — The schema's private policy and extension registry remain writable by resolvers

The code comments claim that the armed policy is reachable from no consumer-visible name. That
is false for the schema object itself. `DjangoSchema` stores the authority in an ordinary
`_resource_policy` entry in `schema.__dict__`, and Strawberry stores the extension list in the
ordinary `extensions` entry. `info.schema` is available to every resolver, so a resolver can write
both without using any undocumented framework hook:

```python
info.schema.__dict__["_resource_policy"] = ResourcePolicy(max_list_rows=999)
info.schema.__dict__["extensions"] = ()
```

I verified both mutations against a live `DjangoSchema` with a two-row policy and 23 Branch rows.
The first request correctly returned two rows. After the resolver replaced `_resource_policy`, the
next request returned 23 rows. After the resolver replaced `extensions`, the next request also
returned 23 rows because the resource extension was no longer instantiated and the field fell
back to the package default. This is a process-lived, cross-request widening and extension-removal
primitive, not a same-request ContextVar race.

The property-copy defense only protects reads through `schema.resource_policy`; it does not
protect direct `__dict__` writes, and the extension auto-installation logic cannot help once the
consumer has replaced its source tuple. This contradicts Spec-047's authority invariant carried
into Spec-050 and the explicit live policy-authority claims in the build plan.

**Root-cause correction:** remove enforcement authority from mutable consumer-reachable schema
attributes. Keep an exact, package-owned policy/extension registry keyed to the schema or an
execution handle, and have every operation resolve the registry entry without consulting mutable
schema `__dict__` state. Freeze or copy the extension configuration at construction, and make
schema lifetime cleanup explicit so the registry cannot leak. Tests must mutate the private
attribute and extension tuple exactly as above, then issue a second real request; testing only
the public property is insufficient.

## P1-3 — Explicit extension policies are not one operation snapshot

`extensions/resource_policy.py::DjangoResourcePolicyExtension._resolved_policy` returns the raw
explicit `_policy` object. `on_operation` passes it through `begin_resource_budget`, which creates a
canonical private snapshot, but `scan_document_text` still receives the raw object. Later,
`on_execute` calls `_resolved_policy()` again and charges the raw object again. Thus the scanner,
the armed budget, and the post-parse/value walk can observe different policies.

This is exploitable with a valid `ResourcePolicy` subclass whose first post-construction read of
`max_document_tokens` is `1` and subsequent reads are `1_000_000`. The canonical snapshot receives
the restrictive value, while the scanner's subsequent reads see the wide value and `{ x }` runs
instead of being rejected as a one-token document. The same pattern can widen selection, value,
collection, or upload bounds. A shared exact policy object is also mutable through its `__dict__`
if the consumer retains the explicit extension instance.

**Root-cause correction:** canonicalize and copy an explicit policy once when the extension
configuration is accepted, then capture that exact object for the complete operation. Both
`on_operation` and `on_execute` must consume the same snapshot (and the extension factory must not
re-read consumer policy attributes per hook). Add an extension-level test with a stateful policy
subclass and a plain `strawberry.Schema`, because the existing schema-construction canonicalization
test does not cover this separate explicit-extension path.

## P1-4 — Value-budget accounting still trusts consumer-controlled shapes

The same exact-type rule used for policy numbers is not propagated through the value walker:

- `extensions/resource_policy.py::_ValueBudget._charge_container` accepts `list`/`tuple` and
  `Mapping` subclasses, calls their dynamic `__len__`, and iterates them directly;
- `_ValueBudget._charge_leaf` accepts `str` subclasses and calls their overridden `encode`;
- the bytes branch evaluates `len(value)` eagerly as the default argument to `getattr`, so a
  bytes subclass can raise before `nbytes` is considered.

Direct probes produced all three failure modes: a list subclass reporting length zero but yielding
100 elements was accepted under `max_container_width=1`; a string subclass whose `encode` returned
one byte was accepted under `max_scalar_bytes=1` despite being 100 characters; and a bytes subclass
whose `__len__` raised escaped as a raw `RuntimeError`. A custom scalar's `parse_value` can return
these subclasses, so this is not limited to an artificial direct call.

**Root-cause correction:** normalize custom-scalar/container values to exact framework-owned
representations before accounting, or reject non-exact sequence/mapping/text/buffer shapes as
unmeasurable. Read a buffer's size through a safe exact-type path without an eagerly evaluated
hostile fallback. Add live custom-scalar probes and package tests for benign and raising subclasses
for every value-bound family; do not add isolated `try` blocks around only the examples above.

## P2-1 — Positive integer policy values have no representability boundary

`resource_policy.py::_require_positive_int` accepts an exact integer of arbitrary magnitude. The
wire-visible `ResourceLimitExceeded` constructor then interpolates `limit` and `charged` directly
with f-strings. A schema policy containing `10**10000` is accepted, but a normal list query reaches
the collection-cost rejection with a built-in `ValueError` from CPython's integer-to-string digit
limit while constructing that supposed typed resource error. With smaller oversized values, the
query reaches SQLite and fails with a backend `IntegrityError` because the generated LIMIT cannot
be represented by the database adapter.

This leaves a configuration that passes schema construction but cannot produce the promised
typed rejection or a valid bounded query. Define and validate a backend-safe magnitude for every
bound that reaches SQL or error payloads, or canonicalize to a documented safe ceiling. Keep the
error renderer safe for all accepted values. Add construction and live execution tests at the
largest accepted magnitude on every supported database backend.

## P2-2 — Verification and test evidence do not certify this tree

The [build record][build-050] records the final default/sharded/floor gate at `207c7328`, then
explicitly says the policy-authority remediation was implemented and **ungated**. The current
production history includes later policy and ordering commits through `17bc2cfb` and the current
`HEAD` is `648214b4`; no full default, sharded, or declared 17-path floor gate is recorded at this
delivery tree. The working tree also contains concurrent uncommitted test/document/database
changes, so the old figures are not a reproducible release proof.

The tests cover ordinary lists and guarded mapping fallback, but there is no adversarial
`__getitem__`-ignoring sequence test, no live materialized-subclass list-field case, and no
stateful explicit-extension-policy test. Those are exactly the public and lifecycle seams that the
probes above break. Under [AGENTS.md][agents], the root production fixes must land with tests in
the correct package/live tiers and the complete gate must be rerun before certification.

## Required disposition

Do not mark Spec-050 complete yet. First close the three P1 authority/accounting defects with
framework-owned representations and one operation snapshot, then add the live/package coverage
for those paths. Re-run the full default, sharded, and declared floor suites at the delivery
commit, update the build record with that exact commit, and only then reassess the lower-severity
representability issue.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[goal]: ../GOAL.md

<!-- docs/ -->
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-050]: builder/DONE/build-050-list_field_arguments-0_0_15.md

<!-- django_strawberry_framework/ -->
[resource-policy]: ../django_strawberry_framework/resource_policy.py
[resource-policy-extension]: ../django_strawberry_framework/extensions/resource_policy.py
[schema]: ../django_strawberry_framework/schema.py
[list-field]: ../django_strawberry_framework/list_field.py

<!-- tests/ -->
[test-resource-policy]: ../tests/test_resource_policy.py

<!-- examples/ -->
[live-readme]: ../examples/fakeshop/test_query/README.md
[test-list-field-api]: ../examples/fakeshop/test_query/test_list_field_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
