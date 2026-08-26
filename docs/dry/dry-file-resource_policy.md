# DRY review: `django_strawberry_framework/resource_policy.py`

Status: verified

## System trace

`resource_policy.py` owns the one immutable per-request execution budget:
`ResourcePolicy` (~20 positive-int bounds plus the optional
`execution_deadline_seconds`), validated once in `__post_init__` so an invalid
policy cannot exist; `narrowed()` as the single statement of the
narrowing-only rule; `resolve_resource_policy()` normalizing the deployment's
choice once at schema construction (`DjangoSchema(resource_policy=...)` arg >
`DJANGO_STRAWBERRY_FRAMEWORK["RESOURCE_POLICY"]` > `DEFAULT_RESOURCE_POLICY`);
context threading via the two `DST_RESOURCE_*` keys over `utils/context.py`;
and the enforcement primitives: `policy_from_info` / `check_deadline` readers,
`bounded_rows` / `bounded_rows_async` raw-list bounds,
`validate_collection_bound` field-factory gate, and `effective_bound`, the
narrowing combinator.

Consumers traced end to end: `schema.py::DjangoSchema` resolves the policy
once and appends `extensions/resource_policy.py::DjangoResourcePolicyExtension`
as a class; the extension spends the document/value budgets pre-parse and
pre-execute and stashes/restores both context keys;
`connection.py::resolve_connection` clamps `relay_max_results` through
`utils/connections.py::resolve_relay_max_results` -> `effective_bound` and
checks the deadline at the head every connection shape passes through;
`list_field.py` routes all four resolver colors through `bounded_rows*`;
`types/resolvers.py` bounds generated many-side relations the same way;
`relay.py` (node/nodes refetch) and `mutations/resolvers.py::
run_write_pipeline_sync` (before the transaction opens; ONE pipeline serves
sync and async resolvers, so there is no async twin to miss) check the
deadline; `conf.py::resource_policy_setting` is the thin reader;
`error_policy.py::resolve_error_policy` is the self-declared structural twin of
the resolver; GLOSSARY/spec-047 restate the posture in prose.

## Verification

Axis 1 - cross-flavor mirroring. Searched `grep -rn "def resolve_"` across the
package: exactly two schema-construction policy resolvers exist, and
`error_policy.py::resolve_error_policy` calls itself "the structural twin" of
`resolve_resource_policy`. Diffed line by line: mechanically identical modulo
four data parameters (class, default, settings reader, message nouns).
Confirmed duplication -> Opportunity 1. Package-wide `grep "positive integer"`:
only this module owns the bound-domain predicate, but twice inside it
(`__post_init__` + `validate_collection_bound`) -> Opportunity 3. No other
flavor (filters/forms/orders/`rest_framework`) carries its own copy of any
bound rule.

Axis 2 - sync/async twins. `bounded_rows` / `bounded_rows_async` compared by
behavior: both spelled the identical two-line seam (`check_deadline(info)` +
`effective_bound(policy_from_info(info).max_list_rows, declared, trusted=...)`)
verbatim -> Opportunity 2. Checked for missed async seams elsewhere: the write
pipeline has no async twin (`run_write_pipeline_sync` serves both resolver
colors via decode/write callbacks), so its single `check_deadline` covers both;
visibility/post-processing twins are already single-sited in
`utils/querysets.py`.

Axis 3 - derived rather than repeated knowledge. The valid-vocabulary set is
derived from `dataclasses.fields()` at each use site - deriving from the owning
declaration, not duplicating it (a hand-maintained list would be the defect).
The three fail-closed default fallbacks (`policy_from_info` context-miss,
`_resolved_policy` schema-attr miss, `schema_error_policy`) share a contract
but not a lookup chain - rejected below.

Axis 4 - inverse/round-trip pairs. `stash_resource_policy` encode /
`policy_from_info` + `check_deadline` decode are keyed on the same two module
constants in the same file. `ResourceLimitExceeded.__init__` /
`__reduce__` pickle pair - rejected below.

Axis 5 - contracts restated in another medium. GLOSSARY entries, spec-047, and
`conf.py` comments restate the resolution posture and the
`RESOURCE_LIMIT_EXCEEDED` literal in prose; they describe rather than
implement, so no generated artifact or second implementation needs lockstep
edits beyond docs.

Single-edit-site counts (posited changes):

- P1 "unknown-key rejection suggests the nearest valid name": forces
  `resolve_resource_policy` + `resolve_error_policy` = 2 sites today; 1 after
  Opportunity 1.
- P2 "raw-list rows additionally capped by `max_page_size`": forces
  `bounded_rows` + `bounded_rows_async` = 2 sites today; 1 after Opportunity 2.
- P3 "widen the bound-domain predicate (e.g. accept integral types)": forces
  `__post_init__` + `validate_collection_bound` = 2 sites today; 1 after
  Opportunity 3.
- Counts that came back ONE (independence proved): adding a NEW bound touches
  only the dataclass declaration plus its new enforcement site - resolution,
  narrowing, vocabulary errors, and threading all derive from `fields()`
  (plumbing count 1); changing the wire code is one constant edit
  (`RESOURCE_LIMIT_ERROR_CODE`; consumers import the symbol).

Strongest rejected candidates:

- `_page_bound`'s `min(value, policy.max_page_size)` vs `effective_bound`:
  coinciding arithmetic, different contracts. `_page_bound` clamps an UNTRUSTED
  wire value with a conservative non-int fallback; `effective_bound` combines
  two trusted declarations under the trusted-widening carve-out.
- Extension-side fallback getters (`_resolved_policy` vs
  `schema_error_policy`): same fail-closed default, different chains
  (constructor override then plain getattr, vs exception-guarded getattr);
  merging needs mode flags for four lines each adjacent to their only consumer.
- The `(DST_RESOURCE_POLICY, DST_RESOURCE_DEADLINE)` pair enumerated in
  `stash_resource_policy`, `clear_resource_context`, and the extension's
  save/restore: three two-line spellings; a loop form saves nothing until a
  third key exists and obscures the save/restore pairing pinned by the
  nested-schema tests.
- `__reduce__`'s explicit argument tuple vs `__init__`: mandated by the pickle
  protocol over a custom multi-arg `__init__` (`BaseException.args` would
  reconstruct wrongly); intra-class adjacency keeps drift risk minimal.
- `clear_resource_context` has no in-package caller (the extension restores
  prior values instead of clearing): it is a module-public consumer surface,
  so removal is an API decision, not a deduplication.

## Opportunities

### 1. One schema-construction policy resolver, stated once

- **Repeated responsibility:** the normalization contract - instance
  passthrough, setting fallback, fail-closed default, mapping-type rejection,
  unknown-key rejection naming the valid vocabulary, keyword construction -
  implemented twice because the error policy was written as a deliberate
  structural twin of the resource policy.
- **Sites:** `resource_policy.py::resolve_resource_policy`,
  `error_policy.py::resolve_error_policy`.
- **Evidence:** P1 above counts 2 forced sites; both docstrings already declare
  the twin contract, so drift between them is a live hazard the prose cannot
  prevent.
- **Owner:** new neutral `utils/policies.py::resolve_policy`
  (`utils/context.py` precedent: a shared seam helper created for two sibling
  subsystems), parameterized by `policy_cls` / `default` / `read_setting` /
  `display_name` / `unit`. The article in "a ResourcePolicy" / "an ErrorPolicy"
  is derived from the class name.
- **Consolidation:** both resolvers become one-line delegations keeping their
  names, signatures, docstrings, and byte-identical messages (verified against
  the originals before editing); `error_policy.py` drops its now-unused
  `fields` import.
- **Proof:** new `tests/utils/test_policies.py` pins the generic ladder
  directly; the existing flavor tests (`tests/test_resource_policy.py`
  precedence-ladder rows, `tests/test_error_policy.py` message regexes) pin
  both wire wordings unchanged.
- **Risks / non-goals:** domain validation stays with each policy's
  `__post_init__`; neither resolver gains or loses precedence behavior.

### 2. One raw-list bound seam for both execution colors

- **Repeated responsibility:** deadline check + effective raw-list limit for
  `max_list_rows`.
- **Sites:** `bounded_rows`, `bounded_rows_async` (verbatim duplicate lines).
- **Evidence:** P2 above counts 2 forced sites; no single test asserts the two
  colors against the same bound change, so drift would be silent.
- **Owner:** module-private `resource_policy.py::_raw_list_bound(info,
  declared, trusted)` calling `check_deadline` then `effective_bound`.
- **Consolidation:** both functions call the helper first (preserving the
  pinned order: the deadline fires even when the result is `None`; the async
  sync-shape delegation still reaches the deadline through `bounded_rows`).
- **Proof:** existing `tests/test_resource_policy.py` `bounded_rows*` rows
  (slicing, unsliceable fallback, trusted widening, `None` passthrough, aclose
  semantics) all pass unchanged; ordering is preserved by construction.
- **Risks / non-goals:** the async prefix-consumption and cleanup-note logic
  stays async-only; lazy querysets keep their SQL `LIMIT`.

### 3. One positive-integer bound-domain predicate

- **Repeated responsibility:** "this knob is a positive integer" (with the
  `bool` trap), stated twice with byte-equal messages.
- **Sites:** `ResourcePolicy.__post_init__` loop tail,
  `validate_collection_bound`.
- **Evidence:** P3 above counts 2 forced sites; both messages are
  `{label} must be a positive integer; got {describe_value(value)}.` differing
  only in the label the caller supplies.
- **Owner:** module-private `resource_policy.py::_require_positive_int(value,
  label)`.
- **Consolidation:** both sites delegate with labels
  `ResourcePolicy.{field.name}` / the factory-supplied `field` string.
- **Proof:** the parametrized constructor-rejection rows and
  `test_a_field_declared_collection_bound_must_be_a_positive_integer` pin both
  messages unchanged. The deadline branch stays separate (different domain:
  optional positive finite number).
- **Risks / non-goals:** non-negative Relay pagination checks
  (`utils/connections.py::assert_relay_pagination_bound`) deliberately stay on
  Strawberry's `SliceMetadata` ValueError vocabulary.

## Judgment

The target's own design is unusually drift-resistant - bounds are declared
once, validated at construction, derived everywhere else, and fail closed -
and most apparent twins dissolved under verification into call sites of a
single owner. What remained real were the three places where one contract was
spelled twice anyway: the schema-construction resolver shared with
`error_policy.py`, the raw-list bound seam shared by the two execution colors,
and the bound-domain predicate shared by construction and factory validation.
All three are now single-sited without changing any wire-visible behavior;
messages were verified byte-identical against the pre-edit source.

## Implementation (Worker 1)

Tracked changes (diffed against cycle baseline
`22bf9a6ed5b53593bd73286a0bd3038979599f7c`, which these files matched at
start; concurrent work elsewhere left untouched):

- NEW `django_strawberry_framework/utils/policies.py` -
  `resolve_policy` (+ `_article`).
- `django_strawberry_framework/resource_policy.py` - resolve_resource_policy
  delegates to `resolve_policy`; added `_require_positive_int` and
  `_raw_list_bound`; `bounded_rows` / `bounded_rows_async` /
  `validate_collection_bound` / `__post_init__` route through them.
- `django_strawberry_framework/error_policy.py` - resolve_error_policy
  delegates to `resolve_policy`; dropped unused `fields` import.
- NEW `tests/utils/test_policies.py` - six rows pinning the shared ladder.
- `docs/TREE.md` - one entry for the new utils module.

Post-edit hygiene: `uv run ruff format .` and `uv run ruff check --fix .` clean
(431 files unchanged / all checks passed); `scripts/check_trailing_commas.py`
fixed 0. Message fidelity proven by direct interpreter runs reproducing all
four original rejection texts byte-for-byte. Pytest NOT run (maintainer
authorization required; deferred to the cycle gate). New untracked module is
invisible to the generated kanban allowlist until commit, when
`scripts/build_kanban_tracked_path_constants.py` picks it up.

## Independent verification (Worker 2)

Verdict: **revision-needed** — every code consolidation is proven equivalent;
the one defect is the docs/TREE.md medium (axis 5), which fails the repo's own
generator gate on this item's account.

**Byte-equivalence of consolidation #1, proved independently.** Extracted both
OLD resolver bodies verbatim from cycle baseline `22bf9a6` via
`git show` + AST source segments (no transcription), executed them in a
namespace holding the real current classes/helpers, and drove OLD and NEW with
identical inputs (`docs/dry/temp-tests/dry-file-resource_policy/
verify_resolve_policy_equivalence.py`). 12 behavior cases across both flavors
(valid mapping, unknown key, non-mapping int/str/list, empty mapping, bool
value, None-explicit setting fallback): messages byte-identical, results equal.
Identity semantics hold: instance passthrough returns the same object; the
default is returned by identity for both flavors. Ladder order and the
`explicit if explicit is not None` guard are preserved verbatim in
`utils/policies.py::resolve_policy`; `_article("ErrorPolicy") = "an"` /
`(ResourcePolicy") = "a"` reproduces both articles; `display_name.replace(' ',
'-')` reproduces both hyphenated vocabularies.

**Consolidations #2/#3 boundaries, probed executable**
(`probe_boundaries.py`): deadline fires BEFORE the `result is None` passthrough
(pinned ordering preserved — raises `RESOURCE_LIMIT_EXCEEDED` for a spent
deadline even with a `None` result); `None` declared / zero / negative declared
flow through `effective_bound`'s pure min/max identically and non-raising on
validated paths (all production call sites pass construction-guarded values:
`list_field.py:179`, or no declared at all); `_require_positive_int` rejects
True/False/0/-1/-100/1.5/'3'/None with byte-exact messages and accepts 1 and
large ints. The early `limit` computation's only theoretical divergence (garbage
`declared` + `None` result raising from `min()` instead of returning `None`) is
unreachable through every annotated call site.

**Coverage sufficiency for `utils/policies.py`:** statement-based gate
(`[tool.coverage.run]` has no branch flag), `fail_under = 100`. The six rows in
`tests/utils/test_policies.py` execute every statement: passthrough (t1),
setting-fallback ternary both arms (t2/t5/t6 vs t2), default return (t2),
mapping-type rejection (t5), unknown-key rejection (t6), construction (t3/t4).
Flavor wire wordings pinned at `tests/test_resource_policy.py:189-200` and
`tests/test_error_policy.py:183-230`. Placement correct: `utils/` shared-seam
precedent; `tests/utils/` tier justified because the rejection paths are
startup failures unreachable from a live `/graphql` query. Module ASCII-clean,
ruff-format clean.

**Matrix discharged (re-probed):** axis 1 - package-wide `def resolve_` sweep:
exactly two schema-construction policy resolvers existed pre-change; the rest
are unrelated field/meta resolvers. Axis 2 - the only sync/async twin pair was
the raw-list seam; the write pipeline serves both colors through one pipeline;
checked `list_field.py` / `types/resolvers.py` call sites for missed seams.
Axis 3 - vocabulary derives from `dataclasses.fields()` at the single owner; no
hand-maintained bound lists. Axis 4 - stash/read pair keyed on the same module
constants in one file; `__reduce__` pickle pair re-probed, protocol-mandated.
Axis 5 - this is where the item fails: TREE.md is a generated medium.

**Single-edit-site recount (own posited change):** "add an env-var override
tier above the setting" forces exactly ONE production site post-change
(`utils/policies.py::resolve_policy`; both delegations inherit), two at
baseline. P3 recount holds: widening the bound-domain predicate now touches
only `_require_positive_int`. Rejected candidates re-probed against real code
and all stand: `_page_bound` clamps an untrusted wire value with a conservative
fallback vs `effective_bound`'s trusted-widening combinator;
`_resolved_policy` vs `schema_error_policy` run different chains over four-line
bodies; the DST key-pair spellings are pairing-pinned two-liners;
`clear_resource_context` has zero in-package callers (consumer surface).

**The revision needed (concrete):** `uv run python scripts/build_tree_md.py
--check` FAILS (CI-gated at `.github/workflows/django.yml:77`) partly on this
item's account. Committed line 299 reads "The shared schema-construction policy
resolver (``resolve_policy``) behind the resource and error policies." but the
generator renders the docstring's first sentence, "Shared schema-construction
policy normalization."; the target-package-layout row (~426) and the
`test_policies.py` rows in both test-tree sections (~580, ~812) are missing
entirely. Every other entry in the file matches generator output exactly -
this item's hand-written line is the sole divergence it owns. Fix: regenerate
`docs/TREE.md` with `scripts/build_tree_md.py` rather than hand-editing.
Note: the regenerated file will also add `test_sessions.py` rows owned by
CONCURRENT work (`tests/utils/test_sessions.py` is new on disk, untracked at
baseline) - that drift is out of this item's scope but the generator owns the
whole section, so folding it in is the tool's own output, not an edit of
concurrent work.

Deferred: pytest (not authorized). Scratch probes retained under
`docs/dry/temp-tests/dry-file-resource_policy/` until cycle closeout.

## Iterations

### Revision 1 (Worker 1) — defect resolved upstream before the edit landed

Arrived to fix the one Worker-2 defect (TREE.md hand-edited instead of
regenerated; `--check` failing on this item's account). While re-baselining,
HEAD advanced and maintainer commit `91989b60` ("docs(tree,agents): record the
single-sourced release and the run's new modules") already regenerated
`docs/TREE.md` through `scripts/build_tree_md.py`, naming this exact defect in
its message. This revision therefore touched zero files and re-verified the
landed state:

- `uv run python scripts/build_tree_md.py --check` exits 0 (was exit 1).
- Every cycle-owned render target is present and docstring-derived, not
  hand-written: `utils/policies.py` in both package trees with the comment
  "Shared schema-construction policy normalization." - the first sentence of
  that module's docstring; `test_policies.py` in both test-tree sections with
  "``utils/policies.py::resolve_policy`` - the shared schema-construction
  resolver." - its module docstring's first line. No source-side docstring
  tweak was needed.
- The regenerated tree also carries `test_sessions.py` rows owned by the
  concurrent session-work flagged at verification time; that work has since
  been committed (`tests/utils/test_sessions.py` tracked at HEAD), so keeping
  them publishes no half-landed feature work - they are the generator's own
  output over settled state.
- `resource_policy.py` / `error_policy.py` tree comments are unchanged by the
  consolidation, matching the render: both resolvers kept their docstrings.
- Ruff format/check deliberately not run: no Python was edited in this
  revision, and a repo-wide pass would rewrite the maintainer's concurrently
  dirty files.

Status set back to `fix-implemented` for Worker 2 re-verification of the
landed render.

### Re-verification (Worker 2) — loop closed

Re-checked after further HEAD movement: `uv run python scripts/build_tree_md.py
--check` passes ("docs/TREE.md is up to date."). All four cycle-owned rows are
present and docstring-derived, matching each module's own docstring verbatim:
`policies.py` "Shared schema-construction policy normalization." at both
package-tree sites (~299, ~426) and `test_policies.py`
"``utils/policies.py::resolve_policy`` - the shared schema-construction
resolver." at both test-tree sections (~580, ~812). Consolidation surfaces
re-probed standing: `resolve_resource_policy` and `resolve_error_policy` are
one-line delegations to `utils/policies.py::resolve_policy`;
`_raw_list_bound` serves both `bounded_rows` / `bounded_rows_async`;
`_require_positive_int` serves both `__post_init__` and
`validate_collection_bound`. Nothing observed contradicts the discharged
matrix; byte-equivalence stands as proven in Independent verification above.
Status set to `verified`. Pytest remains deferred per instructions.
