# Adversarial review: spec-050 candidate

Date: 2026-09-21

Reviewed the committed candidate implementation at `08801efb` (the current branch is
`69a25369`, with only documentation/test commits after that candidate) against the complete
specification, the builder record, `GOAL.md`, `AGENTS.md`, and the live policy/list-field code.
The working tree also has concurrent production edits in `connection.py`, `list_field.py`, and
`utils/querysets.py`; those were not attributed to spec-050 or changed here. The findings below
are against the candidate implementation, not those uncommitted edits.

Verdict: **not ready to close.** There is one release-blocking authority escape, one lower-severity
configuration-domain violation, and no exact-tree gate or evidence-only closeout yet.

## P1 — exported default policies remain live enforcement authorities

### Broken contract

Spec-050 Decision 14 requires configuration to be canonicalized once into private schema state,
with the object a resolver can reach being only a copy. It explicitly rejects a frozen dataclass
as an authority because `__dict__`/`object.__setattr__` can still alter it. The same guarantee is
part of the builder's enforcement-authority rows and the production error-policy contract: a
resolver or ordinary application setup must not be able to widen bounds or turn masking off for
subsequent operations by changing a process-lived policy object.

### Reachable project shape and input

`DEFAULT_RESOURCE_POLICY` and `DEFAULT_ERROR_POLICY` are public exports. A project that uses the
documented default `DjangoSchema(query=...)` needs no private extension wiring and no malformed
GraphQL input. A resolver, startup hook, or other ordinary application code can mutate the public
dataclass instance through its normal `__dict__`:

```python
from django_strawberry_framework import DEFAULT_ERROR_POLICY, DEFAULT_RESOURCE_POLICY

DEFAULT_RESOURCE_POLICY.__dict__["max_list_rows"] = 999
DEFAULT_ERROR_POLICY.__dict__["enabled"] = False
schema = DjangoSchema(query=Query)  # no policy arguments supplied
```

### Evidence

In an isolated fakeshop process on the candidate code:

```text
DEFAULT_RESOURCE_POLICY.max_list_rows: 100 -> 999
DjangoSchema(...).resource_policy.max_list_rows: 999
DEFAULT_ERROR_POLICY.enabled: True -> False
DjangoSchema(...).error_policy.enabled: False
```

The wire consequence is reproducible without any nonstandard transport. With the public default
error policy changed as above, a normal resolver that raises `RuntimeError("SECRET-DEFAULT-POLICY")`
returns that raw message in the GraphQL error response. The schema's automatic masker is disabled
because `resolve_policy(..., default=DEFAULT_ERROR_POLICY)` returns the singleton itself when no
override is configured; `DjangoSchema` then stores that same object in its private record.

The shared resolver has the same identity defect for resources:

```text
mutate DEFAULT_RESOURCE_POLICY.__dict__["max_list_rows"] = 999
resolve_policy(..., default=DEFAULT_RESOURCE_POLICY).max_list_rows == 999
resolve_policy(..., default=DEFAULT_RESOURCE_POLICY) is DEFAULT_RESOURCE_POLICY == True
```

### Root cause

`utils/policies.py::resolve_policy` canonicalizes explicit instances and mappings, but returns
`default` directly on the no-override path. Both `resource_policy.py::DEFAULT_RESOURCE_POLICY` and
`error_policy.py::DEFAULT_ERROR_POLICY` are public mutable dataclass objects despite `frozen=True`.
The private authority therefore holds an object that remains reachable by public import.

### Required fix

Fix the shared owner, not each schema call site:

1. Make the no-override/default branch of `utils/policies.py::resolve_policy` return a fresh,
   validated canonical copy of `default` (the same primitive field read used for explicit policy
   instances), never `default` itself.
2. Ensure `_FALLBACK_ENFORCEMENT` and every default used by the standalone extension path also
   hold private canonical copies, or otherwise ensure no enforcement seam ever reads an exported
   singleton.
3. Keep the public constants as value templates for inspection, but never use them as authority
   objects. Do not weaken the guarantee by merely documenting that callers must not mutate them.
4. Replace identity assertions such as `resolve_resource_policy(None) is DEFAULT_RESOURCE_POLICY`
   and their error-policy twins with equality plus `is not` checks. Add a live `/graphql` row that
   mutates each public default before schema construction and proves the schema still uses the
   package's original bounded/masking defaults; retain the direct resolver pin as a package test.
5. Prove the resource row reaches an actual list-field ceiling and the error row reaches an
   actual unexpected resolver exception. A test that only reads `schema.resource_policy` is not
   enough to establish the wire/configuration boundary.

Until this is fixed, the candidate can silently widen every default raw-list budget and can expose
unexpected resolver exception text in production. This meets Decision 20's admission rule: the
input is a public package configuration object, the schema shape is supported, and the effect is
observable on the GraphQL wire.

## P2 — `ErrorPolicy` does not canonicalize string subclasses to built-in strings

### Broken contract

Decision 14 says policy configuration is canonicalized into exact built-in primitives. The
resource policy enforces that rule for numeric bounds, but `error_policy.py::ErrorPolicy.__post_init__`
uses `isinstance(value, str)` for `message` and `correlation_extension_key`. A consumer-supplied
`str` subclass is therefore accepted and copied into the private enforcement record unchanged.

### Reachable input and evidence

This is ordinary configuration, not a forged GraphQL value:

```python
class StringSubclass(str):
    def __format__(self, spec):
        raise RuntimeError("format hook")

policy = ErrorPolicy(message=StringSubclass("safe"))
schema = DjangoSchema(query=Query, error_policy=policy)
```

The constructor and `utils/policies.py::canonical_policy` both accept the value, and the resolved
policy still contains `StringSubclass`, not exact `str`. The masking path then dispatches the
subclass's formatting hook while building the replacement. Current fail-closed handling prevents
raw text from reaching the client in this particular shape, but it logs/degrades the whole result
instead of honoring the configured policy. A hostile correlation-key subclass similarly turns a
single masked error into a degraded response. The accepted configuration therefore violates its
declared domain and makes normal masking behavior depend on consumer dunder code.

### Required fix

At `ErrorPolicy` construction, require `type(value) is str` for both string fields (and preserve
the existing exact-bool rule for `enabled`). Either reject subclasses with `ConfigurationError`
or normalize them with `str.__str__` into exact strings before constructing the private copy; use
one policy-domain decision consistently with `ResourcePolicy`. Add direct construction tests,
schema-construction tests, and a failability row proving the old `isinstance` acceptance fails.
This is a robustness/configuration finding rather than a separate wire disclosure once P1 is fixed,
because the current masking floor degrades safely.

## P1 — the required exact-tree release gate has not run

This is a release-process blocker independent of the two code findings.

`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md` still says `Status: Candidate`, leaves
the **Final exact-commit gate**, the exact-tree review, and the evidence-only follow-up unchecked,
and explicitly says no gate is recorded. The builder's Decision 22 requires, in order:

1. the candidate implementation commit;
2. the default suite at 100% coverage, sharded suite, declared supported-floor scope, and all
   structural/documentation/citation/tracked-path checks on that exact commit;
3. this adversarial review on that exact tree, with any admitted finding looping back through a new
   candidate; and
4. an evidence-only follow-up whose parent is the gated candidate and whose only file change is
   the build record.

The candidate implementation commit is identifiable from history as `08801efb`; the build record
does not name that SHA, and the current branch has later commits plus concurrent dirty production
files. Historical suite numbers and checks from other trees cannot discharge this gate. Do not mark
the card DONE or write a green follow-up until the P1 authority fix is in a new candidate and all
required commands are run against that exact parent.

## What this review did not classify as a new spec defect

- The uncommitted `connection.py`, `list_field.py`, and `utils/querysets.py` edits are concurrent
  work and were not folded into this candidate review. They must receive their own attribution and
  verification before any final gate that runs on the working tree.
- The build record's documented deferred connection-sidecar filter seal and the foreign evaluated
  queryset-cache case remain explicitly outside this card's Decision 20 trust boundary; they are
  separate work/robustness items, not silently accepted as spec-050 closure evidence.
- The candidate's exact `F`/`Q` type boundary and selected-ordering classifier changes are
  structurally consistent with Decision 6. They are not evidence that the final gate has passed.

## Required disposition

Fix the default-policy authority at the shared policy resolver, tighten `ErrorPolicy`'s primitive
domain, add live/package failability coverage for both, create the resulting candidate commit,
then run the complete Decision 22 gate and repeat this review against that exact commit. Until the
gate and evidence-only follow-up exist, spec-050 remains a candidate rather than a closed release.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../AGENTS.md
[goal]: ../GOAL.md

<!-- docs/ -->

