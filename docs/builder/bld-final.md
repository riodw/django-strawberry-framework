# Build: final test-run gate — list_field_arguments / 0.0.15 (050)

Spec reference: [`docs/spec-050-list_field_arguments-0_0_15.md`][spec-050].
Build plan: [`docs/builder/build-050-list_field_arguments-0_0_15.md`][build-050].
Cycle artifacts: [`bld-slice-1-argument_normalization.md`][bld-s1],
[`bld-slice-2-orderby_pipeline.md`][bld-s2],
[`bld-slice-3-sql_and_unit_contracts.md`][bld-s3],
[`bld-slice-4-live_acceptance.md`][bld-s4],
[`bld-slice-5-documentation_fold_in.md`][bld-s5],
[`bld-integration.md`][bld-int].
Status: final-accepted

## Artifact shape: one Worker 1 pass

This is the `## Final test-run gate` of [`docs/builder/BUILD.md`][build-md], executed after the
Cross-slice integration pass reached `integration-accepted` and subsequent gate re-loop remediation
passes for Slice 4 and Slice 2 reached `final-accepted`. It is a single Worker 1 pass, so the
template's `## Build report (Worker 2)` and `## Review (Worker 3)` sections have no owner here and
are not stubbed. The gate executes the command list in the exact order specified by
[`docs/builder/BUILD.md`][build-md], performs floor verification in an isolated venv outside the
repo, records every pass/fail outcome, and compiles the `### Deferred work catalog`.

Every figure below was measured directly during this re-run pass.

## Gate results

[`docs/builder/BUILD.md`][build-md] `## Final test-run gate`, in declared order.

| # | Command | Result | Verdict |
| --- | --- | --- | --- |
| 1 | `uv run pytest --no-cov` | `7601 passed, 40 skipped in 85.59s`, exit **0** | **PASS** |
| 2a | `uv run python examples/fakeshop/manage.py check` | `System check identified no issues (0 silenced).`, exit **0** | **PASS** |
| 2b | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | `No changes detected`, exit **0** | **PASS** |
| 3a | `uv run ruff format --check .` | `442 files already formatted`, exit **0** | **PASS** |
| 3b | `uv run ruff check .` | `All checks passed!`, exit **0** | **PASS** |
| 3c | `git diff --check` | clean diff, exit **0** | **PASS** |
| 4 | Floor verification | isolated `/tmp/dsf-floor` (Py 3.10.19, Dj 5.2.16, SG 0.316.0); 955 passed in 26.48s; shared `.venv` unmutated | **PASS** |

---

### 1. `uv run pytest --no-cov` — full sweep

Result: `7601 passed, 40 skipped in 85.59s` (exit code **0**).
Command ran with `--no-cov` per `BUILD.md` instructions; no coverage flags were passed and no line
coverage was inspected or asserted.

All failures and warnings encountered in the initial gate pass were resolved by the gate re-loop
remediation passes:

#### Remediation of Failure 1: CI governance extension-form rule violation

- **Initial defect**: Bare class `extensions=[DjangoOptimizerExtension]` in
  `examples/fakeshop/test_query/test_list_field_async_api.py:242` violated `spec-029` Decision 3 and
  `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`.
- **Resolution**: Remediated in Slice 4 gate re-loop pass. Replaced bare-class instantiation with
  conforming singleton factory form `optimizer = DjangoOptimizerExtension()` and
  `extensions=[lambda: optimizer]`.
- **Verification**: `test_no_active_source_uses_a_forbidden_optimizer_extensions_form` passes cleanly.

#### Remediation of Failure 2: Nested async resolver completion with `_AsyncQuerySetRows`

- **Initial defect**: In `tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo`,
  `_AsyncQuerySetRows` implements `__aiter__` without `__iter__`, triggering `graphql-core`'s
  experimental `AsyncIterable` branch in `ExecutionContext.complete_list_value`. Because
  `async_iterable_to_list` returned `complete_list_value` without awaiting when child items are
  awaitable, inner `get_completed_results()` coroutines were returned unawaited, causing `TypeError:
  'coroutine' object is not subscriptable` and leaked coroutine warnings.
- **Resolution**: Remediated in Slice 2 gate re-loop pass. Implemented a wrapper for
  `ExecutionContext.complete_list_value` in `django_strawberry_framework/_strawberry_patches.py` gated
  under `upstream_patches_enabled("strawberry")`. When the result is an `AsyncIterable` (and not a
  standard sync iterable), it resolves items to `sync_result`, delegates to `complete_list_value`,
  and awaits `completed` if awaitable.
- **Verification**: `test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo` and
  surrounding relay connection tests pass with 0 errors and 0 leaked coroutines.

---

### 2. Django's own consistency checks

#### 2a. System checks

Command: `uv run python examples/fakeshop/manage.py check`
Output:
```text
System check identified no issues (0 silenced).
```
Verdict: **PASS** (exit code 0).

#### 2b. Model and migration drift

Command: `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`
Output:
```text
No changes detected
```
Verdict: **PASS** (exit code 0).

---

### 3. Read-only lint/format/diff checks

#### 3a. Ruff format check

Command: `uv run ruff format --check .`
Output:
```text
442 files already formatted
```
Verdict: **PASS** (exit code 0).

#### 3b. Ruff lint check

Command: `uv run ruff check .`
Output:
```text
All checks passed!
```
Verdict: **PASS** (exit code 0).

#### 3c. Git diff check

Command: `git diff --check`
Output: (empty)
Verdict: **PASS** (exit code 0, no whitespace errors or merge conflict markers anywhere in tree).

---

### 4. Floor verification

Floor verification was conducted in an isolated virtual environment created outside the repository
at `/tmp/dsf-floor` using Python 3.10.19.

#### Floor environment construction

```shell
uv venv /tmp/dsf-floor --python 3.10
uv pip install --python /tmp/dsf-floor/bin/python -e . --group dev
uv pip install --python /tmp/dsf-floor/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'
```

#### Resolved versions (`uv pip list --python /tmp/dsf-floor/bin/python`)

- Python: **3.10.19**
- `django`: **5.2.16**
- `strawberry-graphql`: **0.316.0**
- `graphql-core`: **3.2.12**
- `channels`: **4.3.2**
- `cross-web`: **0.7.0**
- `asgiref`: **3.12.1**
- `django-strawberry-framework`: **0.0.15** (editable)

#### Shared `.venv` integrity check

Checked `uv pip list` in the shared `.venv`:
- `django`: **6.1**
- `strawberry-graphql`: **0.324.0**
Confirmed the shared `.venv` was untouched and unmutated during floor verification.

#### Focused scope execution

Command:
```shell
/tmp/dsf-floor/bin/python -m pytest tests/base/test_init.py tests/test_list_field.py tests/test_resource_policy.py tests/orders/test_sets.py tests/utils/test_querysets.py tests/optimizer/test_extension.py tests/test_strawberry_patches.py examples/fakeshop/test_query/test_list_field_api.py examples/fakeshop/test_query/test_list_field_async_api.py examples/fakeshop/test_query/test_resource_policy_api.py --no-cov
```

Output:
```text
============================= 955 passed in 26.48s =============================
```
Verdict: **PASS** (exit code 0).

---

### Deferred work catalog

Audited every per-slice artifact (`bld-slice-1` through `bld-slice-5`) and the cross-slice
integration artifact (`bld-integration.md`):
- `bld-slice-1-argument_normalization.md`: 0 deferred items.
- `bld-slice-2-orderby_pipeline.md`: 0 deferred items.
- `bld-slice-3-sql_and_unit_contracts.md`: 0 deferred items.
- `bld-slice-4-live_acceptance.md`: 0 deferred items.
- `bld-slice-5-documentation_fold_in.md`: 0 deferred items.
- `bld-integration.md`: 0 deferred items.

No deferred work; the build delivered the spec end-to-end.

---

### Gate verdict

All gate commands and floor verifications have passed with zero errors, zero warnings, zero
regressions, and zero unaddressed defects. Card 050 (`docs/spec-050-list_field_arguments-0_0_15.md`)
is fully verified and accepted.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[build-050]: build-050-list_field_arguments-0_0_15.md

<!-- docs/ -->
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build-md]: BUILD.md
[bld-s1]: bld-slice-1-argument_normalization.md
[bld-s2]: bld-slice-2-orderby_pipeline.md
[bld-s3]: bld-slice-3-sql_and_unit_contracts.md
[bld-s4]: bld-slice-4-live_acceptance.md
[bld-s5]: bld-slice-5-documentation_fold_in.md
[bld-int]: bld-integration.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
