# DRY review: project integration

Status: verified

## System trace

Package-wide pass across public exports and representative behaviors that no
single file owns visibly.

**Public surfaces re-read.** Root [`__init__.py`][pkg-init] (eager GraphQL /
mutation / optimizer / schema exports + lazy DRF soft-exports via
`require_drf`); [`types/__init__.py`][types-init] (`DjangoType` /
`finalize_django_types` / `SyncMisuseError`); [`testing/__init__.py`][testing-init]
(HTTP clients + `safe_wrap_connection_method`; Relay helpers stay on the dotted
`testing.relay` path); [`utils/__init__.py`][utils-init] (narrow relation /
string / unwrap facade; substrates stay submodule-owned).

**Representative axes traced.**

| Axis | Owner seam | Cross-boundary notes |
| --- | --- | --- |
| Query | `connection` / `list_field` / `optimizer` | Window contracts in `utils/connections`; visibility seal in `utils/querysets`; one `TypeRegistry` + `register_subsystem_clear` |
| Write | `mutations` / `forms` / RF + `schema` atomic | Shared decode spine in `utils/write_values`; `build_and_stash_input` shared; `cached_build_input` form-only (pre-key) |
| Auth session | `auth/sessions` + `consumers` | `session_store_class` in utils; feature-keyed Channels install hint |
| Filters / orders | `filters` / `orders` + `utils/input_values` | Per-family `INPUTS_MODULE_PATH`; shared `make_input_namespace` / `iter_input_items` |
| Settings | [`conf.py`][conf] | Single `DJANGO_STRAWBERRY_FRAMEWORK` accessor; keys validated at read sites |

**ITEM_BASELINE** `8c48a3e671d4852fda8a770e51e89335de5ab82a`. Concurrent dirt outside
this item left untouched. Plan checkbox not edited (Worker 2).

## Verification

Deferred leads evaluated against present-day source (not prior DRY prose). Live
Trac #37064 page fetched: closed **Bug (invalid)** (Natalia Bidart). Greps for
`MODULE_PATH`, Channels install hints, multipart `operations`/`map`,
`cached_build_input`, relation-annotation twins, `resolved_relation_annotation`,
`type_check_relation_id`, `FilterSet._iter_input_items`, `global_id_for`, plus
independent sweeps for parallel registries, settings interpretation, and
sync/async mirrors.

### Deferred leads — disposition

1. **MODULE_PATH literals / Channels install-hint pairs — reject merge.**
   Each family owns its `strawberry.lazy` module string
   (`filters`/`orders`/`mutations`/`forms`/`rest_framework`/`auth`). Shared
   machinery is already `utils/inputs.py::make_input_namespace`. Collapsing
   path constants would invent a false owner. Channels ABSENT hints in
   [`routers.py`][routers] vs [`auth/sessions.py`][auth-sessions] intentionally
   name different entry features; both call
   `utils/imports.py::require_optional_module` with their own hint. Same floor
   version string (`channels>=4.3.2`) is documentation agreement with
   pyproject/spec, not duplicated package policy worth a shared constant module.

2. **multipart `"operations"`/`"map"` (views vs testing client) — reject merge.**
   [`views.py`][views] owns `_MULTIPART_CONTROL_FIELDS` for server-side lossy-
   decode refusal; [`testing/client.py`][testing-client] builds the client
   envelope and guards reserved `files=` keys. Same GraphQL Multipart Request
   Spec vocabulary, different responsibilities (validate vs produce). Sharing
   would couple the test client to the HTTP view (or invent a protocol-constants
   home for two external-spec literals). External protocol names, not
   package-owned policy.

3. **`wontfix` → `invalid` Trac disposition — reject (reverted).**
   Trac's resolution field is `invalid`. That is Django refusing the
   `isinstance` guard and kicking it to every cursor wrapper (ticket
   comment 25), not a finding that the crash is not a bug. Package
   comments, GLOSSARY, and CHANGELOG keep `wontfix`. A later W1 string
   swap to `invalid` was reverted.

4. **`cached_build_input` docstring claiming form+serializer share — accept.**
   Forms call it; serializer explicitly does not (`rest_framework/sets.py` P1.7
   note: post-build descriptor key). Docstring updated to name form (pre-key
   flavors) and point shared tail at `build_and_stash_input`.

5. **`serializer_only_relation_annotation` ↔ `_model_less_relation_annotation`
   — reject merge.** Same Relay-vs-raw-pk *idea*, different contracts: form
   returns `(attr, annotation)` with optional `registry.get`; serializer returns
   `(attr, annotation, related_model)`, requires primary via
   `_require_relation_primary` (M3), and names serializer-shaped errors. Merging
   needs mode flags that hide distinct fail-loud paths. Shared pieces already
   live at `implements_relay_node` / `scalar_for_field`.

6. **`registry.py` docstring path for `resolved_relation_annotation` — accept.**
   Symbol lives in [`types/converters.py`][converters]; docstring said
   `types.finalizer`. Corrected.

7. **`optimizer/predicates.py` placement — confirm keep.** Pure ORM `EXISTS`
   attachment; knows nothing about GraphQL/types. Callers are filter applicators
   (and future search). Staying under `optimizer/` matches its ORM/plan-adjacent
   charter; not a utils/types split.

8. **Dead `type_check_relation_id` re-export in `mutations/resolvers.py` —
   accept delete.** Owner is `utils/write_values.py`. Forms/RF import from there;
   no remaining importer or test hits the mutations re-export (`# noqa: F401`
   was a lie). Removed.

9. **Stale `FilterSet._iter_input_items` ownership docstring — accept.**
   Owner is `utils/input_values.py::iter_input_items`; `utils/permissions`
   only re-exports. Docstring corrected.

10. **Broader `global_id_for` adoption in hand-rolled GlobalID test sites —
    reject as project DRY.** Helper encodes strategy-aware *emission* for
    finalized Relay nodes. Many hand-rolled sites intentionally mint wrong-type,
    synthetic, model-label, or decode-only payloads that must not go through
    strategy stamping. That is independent fixture hygiene, not duplicated
    encode policy. Where suites already need live strategy parity they import
    `global_id_for`.

### Other package-wide candidates checked

- **Parallel subsystem registries:** one `TypeRegistry` +
  `register_subsystem_clear` / `iter_subsystem_clears`. No second registry.
- **Settings interpretation:** single `conf.settings` + per-key consumers; no
  divergent readers inventing alternate dict walks.
- **Error / naming policy:** write `FieldError` spine and
  `utils/errors` / `utils/strings` already single-site the shared leaves;
  flavor-specific wording stays at flavors.
- **Mirrored sync/async:** views/schema/consumers keep transport-required dual
  methods; shared rules sit in helpers (`require_optional_module`, body gates,
  write pipeline under `sync_to_async`). No new consolidation without hiding
  transport asymmetry.

## Opportunities

### 1. Trac #37064 disposition string — rejected / reverted

- **Repeated responsibility:** one upstream-ticket outcome claim.
- **Sites:** `_django_patches.py`, `testing/_wrap.py`, `tests/test_django_patches.py`,
  GLOSSARY, CHANGELOG `0.0.7`.
- **Evidence:** Trac resolution field is `invalid`; ticket comment 25 is the
  engineering outcome (Django will not own the guard).
- **Owner:** package comments keep `wontfix` as that outcome. GLOSSARY /
  CHANGELOG already matched.
- **Consolidation:** none. The `wontfix` → `invalid` string swap was reverted.
- **Proof:** documentary. Deferred pytest.
- **Risks / non-goals:** do not soften the package's isinstance guard; do not
  echo Django's denial as the package's description of the bug.

### 2. `cached_build_input` ownership prose

- **Repeated responsibility:** which flavors share the pre-build cache helper.
- **Sites:** `mutations/sets.py::cached_build_input` docstring vs
  `forms/sets.py` (caller) vs `rest_framework/sets.py` (non-caller, documented).
- **Evidence:** serializer path comments already explain non-use.
- **Owner:** `mutations/sets.py` docstring.
- **Consolidation:** docstring rewritten; no call-graph change.
- **Proof:** documentary. Deferred pytest.
- **Risks / non-goals:** do not force serializer through pre-build lookup.

### 3. Registry → converters docstring path

- **Repeated responsibility:** symbol location of
  `resolved_relation_annotation`.
- **Sites:** `registry.py` module docstring (fixed).
- **Evidence:** definition in `types/converters.py::resolved_relation_annotation`.
- **Owner:** `registry.py` docstring.
- **Consolidation:** path corrected.
- **Proof:** documentary.
- **Risks / non-goals:** none.

### 4. Dead `type_check_relation_id` re-export

- **Repeated responsibility:** import path for the structural relation-id check.
- **Sites:** dead re-export in `mutations/resolvers.py`; live owner
  `utils/write_values.py`; RF imports owner directly.
- **Evidence:** no remaining importers of the re-export; `# noqa: F401`.
- **Owner:** `utils/write_values.py`.
- **Consolidation:** drop re-export.
- **Proof:** import graph. Deferred pytest (no behavior change).
- **Risks / non-goals:** keep `coerce_relation_pk_or_none` alias used in-file.

### 5. `FilterSet._iter_input_items` ownership docstring

- **Repeated responsibility:** which utils module owns input walking.
- **Sites:** `filters/sets.py` method docstring (fixed).
- **Evidence:** definition in `utils/input_values.py`; permissions re-export.
- **Owner:** docstring at the thin FilterSet delegate.
- **Consolidation:** name `input_values` as owner.
- **Proof:** documentary.
- **Risks / non-goals:** keep permissions re-export for historical imports.

## Judgment

Five documentary / dead-export consolidations landed. Six deferred leads
rejected with present-day evidence (MODULE_PATH, Channels hints, multipart
literals, relation-annotation twins, predicates placement, `global_id_for`
test adoption). No parallel registry or settings-interpretation split found.
Package comments keep Trac #37064 as `wontfix` (Django kicked the guard
downstream; Trac's `invalid` field is not the package's description).

## Implementation (Worker 1)

**Changed**

| Path | Change |
| --- | --- |
| `django_strawberry_framework/_django_patches.py` | `wontfix` kept (see Iterations) |
| `django_strawberry_framework/testing/_wrap.py` | same |
| `tests/test_django_patches.py` | same |
| `django_strawberry_framework/mutations/sets.py` | `cached_build_input` docstring |
| `django_strawberry_framework/registry.py` | converters path in docstring |
| `django_strawberry_framework/mutations/resolvers.py` | drop dead `type_check_relation_id` re-export |
| `django_strawberry_framework/filters/sets.py` | `_iter_input_items` ownership docstring |
| `docs/dry/dry-project.md` | this artifact |

**Kept separate:** per-family MODULE_PATH; feature-keyed Channels hints;
views vs client multipart roles; form vs serializer model-less relation
helpers; `optimizer/predicates.py` placement; hand-rolled GlobalID fixtures.

**Validation:** `uv run ruff format .` and `uv run ruff check --fix .` clean.
Pytest deferred (maintainer authorization required). No permanent test added —
changes are docstring/comment accuracy plus an unused import removal.

**Changelog:** no — documentary / dead-export only; AGENTS forbids unsolicited
CHANGELOG edits.

**Scoped diff statement:** item-scoped edits vs
`8c48a3e671d4852fda8a770e51e89335de5ab82a` are exactly the seven paths above
plus this artifact (`7 files changed, 36 insertions(+), 26 deletions(-)` on
the Python/test set before counting the new artifact). Concurrent dirty files
outside those paths are not part of this item.

**Remaining maintainer decisions**

1. Authorize `uv run pytest` at the cycle gate (deferred here).

Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced package-wide axes and each accepted/rejected lead against present-day
source + live Trac; did not rely on Worker 1 prose alone.

**Scoped diff / concurrent absorption.** Claimed W1 set vs
`8c48a3e671d4852fda8a770e51e89335de5ab82a` is exactly the seven Python/test
paths in Implementation (`7 files, +36/-26`). Full
`django_strawberry_framework/ tests/` diff also shows concurrent
`_strawberry_patches.py`, `schema.py`, and
`tests/mutations/test_write_transaction.py` — not claimed, not absorbed.

**Accepted consolidations**

1. **Trac #37064 `wontfix` → `invalid` — later reverted.** Trac's field
   is `invalid`; that is Django kicking the `isinstance` guard downstream
   (ticket comment 25). Package + tests + GLOSSARY + CHANGELOG keep
   `wontfix`. Hardening behavior unchanged.

2. **`cached_build_input` docstring.** Forms call it
   (`forms/sets.py`); serializer documents non-use and rides
   `build_and_stash_input` only (`rest_framework/sets.py` P1.7). Docstring
   now matches that split.

3. **`resolved_relation_annotation` path.** Defined in
   `types/converters.py`; `registry.py` docstring now names converters.
   No remaining `types.finalizer.resolved_relation_annotation` in package
   source.

4. **Dead `type_check_relation_id` re-export.** Baseline had `# noqa: F401`
   re-export in `mutations/resolvers.py`. Owner remains
   `utils/write_values.py`; RF imports there; forms use
   `decode_visible_relation` (which calls the owner internally) — no
   importer of the mutations re-export. Drop is correct. Replacement comment
   slightly overstates “form … import `type_check_relation_id` directly”;
   non-blocking.

5. **`FilterSet._iter_input_items` ownership.** Body delegates to
   `iter_input_items` imported via `utils/permissions` re-export; true
   definition is `utils/input_values.py`. Docstring now names that owner.

**Rejected leads — challenged, still reject**

| Lead | Challenge evidence |
| --- | --- |
| MODULE_PATH collapse | Per-family `strawberry.lazy` strings (`filters`/`orders`/`mutations`/`forms`/`rest_framework`/`auth`); shared machinery already `utils/inputs.py::make_input_namespace`. |
| Channels install hints | `routers.py` names `DjangoGraphQLProtocolRouter`; `auth/sessions.py` names auth session boundary; both call `require_optional_module` with feature-local hints; floor string is docs agreement. |
| multipart `operations`/`map` | `views.py::_MULTIPART_CONTROL_FIELDS` validates server decode; `testing/client.py` builds/guards the client envelope — produce vs refuse. |
| form↔serializer model-less relation twins | Form returns `(attr, annotation)` + optional `registry.get`; serializer returns `(attr, annotation, related_model)` + `_require_relation_primary` and serializer-shaped errors. Shared leaves already `implements_relay_node` / `scalar_for_field`. |
| `optimizer/predicates.py` | Pure ORM `EXISTS` attachment; callers are filter applicators (search later). No GraphQL/types knowledge — keep under optimizer. |
| Broad `global_id_for` adoption | Helper is strategy-aware emission for finalized Relay nodes. Many hand-rolled sites mint wrong-type, model-label, empty, or decode-only payloads that must bypass strategy stamping. |

**Missed package-wide splits.** Independent sweeps: one `TypeRegistry` +
`register_subsystem_clear`; single `conf.settings` accessor with per-key
readers; write `FieldError` / `utils/errors` / `utils/strings` already
single-site shared leaves; transport sync/async duals remain transport-owned.
No additional consolidation warranted for this pass.

**Validation.** Documentary / dead-export only; pytest deferred to cycle gate
(maintainer). No permanent-test gap for these edits.

**Checkbox.** Marking plan Project integration `[x]`.

**Remaining maintainer decisions (unchanged)**

1. Authorize `uv run pytest` at the final gate.

## Iterations

### Maintainer correction — keep `wontfix`

Trac's resolution field is `invalid` (Natalia Bidart). That is Django
refusing the `isinstance` guard and kicking the can to every cursor
wrapper (ticket comment 25), not a finding that the crash is not a bug.
Package comments, GLOSSARY, and CHANGELOG `0.0.7` already named that
outcome `wontfix`. Echoing Trac's `invalid` in `_django_patches.py`,
`testing/_wrap.py`, and `tests/test_django_patches.py` was wrong and is
reverted. No glossary DB re-render; no CHANGELOG edit.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelog]: ../../CHANGELOG.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[conf]: ../../django_strawberry_framework/conf.py
[converters]: ../../django_strawberry_framework/types/converters.py
[pkg-init]: ../../django_strawberry_framework/__init__.py
[routers]: ../../django_strawberry_framework/routers.py
[testing-client]: ../../django_strawberry_framework/testing/client.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[types-init]: ../../django_strawberry_framework/types/__init__.py
[utils-init]: ../../django_strawberry_framework/utils/__init__.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
