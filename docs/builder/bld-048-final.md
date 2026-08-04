# bld-048-final: final test-run gate

Status: final-accepted

Spec: [`docs/spec-048-secure_output_defaults-0_0_17.md`][spec-048]
Plan: [`docs/builder/build-048-secure_output_defaults-0_0_17.md`][plan-048]
Card: `TODO-ALPHA-048-0.0.17`

## What shipped

### Slice 1 - the filesystem path leaves the default output

`django_strawberry_framework/types/converters.py`

- `DjangoFileType` is now `name` / `size` / `url`; `DjangoImageType` adds `width` / `height`. Neither carries `path`.
- `_FileSystemPathFields` - a private `@strawberry.type`-decorated mixin holding the **single** definition of the opt-in `path` resolver and its security description. The decorator is load-bearing: Strawberry collects inherited fields only from bases carrying a type definition, so an undecorated mixin's `path` would have vanished from both compositions silently. Verified empirically before the shape was chosen.
- `DjangoFilePathType(DjangoFileType, _FileSystemPathFields)` and `DjangoImagePathType(DjangoImageType, _FileSystemPathFields)` - the two public opt-in siblings, root-exported.
- `FILESYSTEM_PATH_OUTPUT_TYPE_MAP` keyed on the **default output type**, not on the Django field class again. Keying it on the field class would have duplicated the MRO walk and let the two maps disagree about what a consumer `ImageField` subclass resolves to.
- `convert_field_output(..., expose_filesystem_path=False)` performs the swap inside the file branch only.

`django_strawberry_framework/types/base.py`

- `Meta.filesystem_path_fields` added to `ALLOWED_META_KEYS`, normalized in `_validate_meta` through the same `_normalize_sequence_spec` guard the two nullability keys use, carried on `_ValidatedMeta`, and threaded into `_build_annotations`.
- `_validate_filesystem_path_targets` - the structural sibling of `_validate_nullability_override_targets`, reusing `_selected_meta_targets` for the shared unknown-name and not-selected guards, and adding the two domain checks: a consumer-authored column (whose own annotation already owns the output type) and a non-file column. Four rejections total, all at type-creation time.

`_safe_file_attr` is **unchanged**. Its narrow `(ValueError, OSError, NotImplementedError)` catch and the propagating `SuspiciousFileOperation` are the same guard they were; removing the field from the default is not a substitute for it, and the audit's "do not mask path failures while exposing successful absolute paths" is satisfied by the removal rather than by widening the catch.

### Slice 2 - the debug extension fails closed and caps its payload

`django_strawberry_framework/extensions/debug.py`

- `__init__(self, *, allow_unsafe_production: bool = False)` - the `__init__` the class lacked. Keyword-only with the safe default, so Strawberry's zero-argument construction of a bare class entry produces the refusing instance and acknowledging is something a deployment must spell.
- `_disclosure_permitted()` reads `settings.DEBUG` per operation. When it is false without the acknowledgement, `on_operation` acquires no bracket, snapshots no query log, builds no payload, and logs one WARNING - then yields and returns. The operation itself is untouched.
- `_truncate` / `_row_cost` / `_apply_payload_caps` plus six limit constants and one shared `_TRUNCATION_MARKER`. Three fixed passes: per-row truncation, row-count caps keeping the earliest rows, then one shared character budget spending on exception rows before SQL rows and **stopping** at the first over-budget row rather than skipping it.

### Slice 3 - the production error policy

- `django_strawberry_framework/error_policy.py` (new) - `ErrorPolicy` (frozen, self-validating), `DEFAULT_ERROR_POLICY`, `resolve_error_policy`, `new_correlation_id`.
- `django_strawberry_framework/conf.py` - `ERROR_POLICY_KEY` + the `error_policy_setting()` thin reader.
- `django_strawberry_framework/extensions/error_policy.py` (new) - `DjangoErrorPolicyExtension`, `_is_unexpected`.
- `django_strawberry_framework/schema.py` - `DjangoSchema(error_policy=...)`, `schema.error_policy`, and `_with_error_policy_extension`.

## Decisions taken on the card's two open questions

**The opt-in shape for an explicit filesystem-path field.** A per-column `Meta` key, `Meta.filesystem_path_fields`, not a server-only field and not a settings flag. Rejected alternatives:

- **A schema-wide setting.** One key silently re-arms every schema in the process and is not auditable per column. A reviewer reading the type would learn nothing about what it publishes.
- **A consumer-authored `strawberry.field`.** Already possible and still supported, but undiscoverable, and it forces the consumer to re-implement the storage guard - which is where the `SuspiciousFileOperation` distinction lives.
- **A marker on the Django model field.** Changing a model to alter a GraphQL surface is the wrong layer.
- **Deleting `path` outright.** A real filesystem-path consumer exists; with no supported route they fork the type and lose the guard with it.

**Correlation-id format, log destination, and message configurability.** `uuid.uuid4().hex` (32 lowercase hex characters), **one per masked error** rather than per operation - a response with two unrelated failures logs two exceptions, and a shared id would make the log ambiguous exactly when an operator most needs it not to be. Logged through the package logger `django_strawberry_framework` at `ERROR` with `exc_info` set to the original exception and the id in the message text, so a plain-text grep resolves it. The message is configurable through `ErrorPolicy.message` (constructor argument or the `ERROR_POLICY` setting) and interpolates nothing from the original by construction.

Two further decisions worth naming because a reader's first instinct is the alternative:

- **Fail-closed means inert, not raising.** Raising at operation start would convert a diagnostics misconfiguration into a total production outage and hand an attacker a denial-of-service lever, while non-disclosure - which is what fail-closed means for a disclosure feature - is already achieved by inertness. The warning is what stops it being silent.
- **The extension is PREPENDED, not appended.** `on_operation` teardowns unwind LIFO, so the first-listed extension finishes last. Masking has to run after every extension that reads `GraphQLError.original_error` - `DjangoDebugExtension` in particular, which is documented to be listed after any masking extension. Appending would have silently emptied its `exceptions` list on any schema installing both. This is the exact inverse of `_with_resource_policy_extension`'s append, because that policy gates *before* execution.

## A consequence worth stating plainly

The structural classification masks **upstream** argument-validation `ValueError`s. Strawberry's own relay code raises `ValueError("Negative indexing is not supported.")` and `ValueError("... cannot be higher than N")` for a bad cursor or an over-large page, and those are indistinguishable from an internal bug at the boundary - which is the whole virtue of the rule: it does not try to guess. Under `DEBUG=False` a client sending a negative cursor now receives the policy message plus a correlation id rather than the pipeline's own text.

That is the correct trade for this card (a rule that guesses fails open), but it is a real ergonomics cost, and the route to recovering it is for the package to raise those rejections as `GraphQLError` rather than to loosen the classification. Recorded here as deferred work rather than absorbed silently.

## Gate results

| Command | Result |
|---|---|
| `uv run pytest --no-cov` | **5463 passed, 42 skipped** in 89.17s |
| `uv run pytest` (the coverage gate) | 5462 passed, 42 skipped; `django_strawberry_framework` at **100%** after the third-classification-branch row below was added. The run recorded 99.99% with `extensions/error_policy.py` line 73 - the `original_error is None` branch - uncovered: a parse or validation failure early-returns before `on_operation` classifies anything, so the only way to reach it is an error graphql-core raises DURING execution. `tests/test_error_policy.py::test_an_execution_error_with_no_originating_exception_is_left_alone` pins it, and a targeted re-run reports both new modules at 100%. |
| `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py --no-cov` | 9 passed |
| `uv run python examples/fakeshop/manage.py check` | System check identified no issues (0 silenced) |
| `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | No changes detected |
| `uv run ruff format --check .` | pass |
| `uv run ruff check .` | All checks passed |
| `git diff --check` | clean |
| `uv run python scripts/check_trailing_commas.py --check .` | pass |
| `uv run python scripts/check_spec_glossary.py --spec docs/spec-048-...md` | `OK: 48 terms` |
| `uv run python scripts/build_tree_md.py --check` | up to date |

## Floor verification

Floor venv built outside the repo at `/tmp/dsf-floor48`, Python **3.10.19**, Django **5.2**, strawberry-graphql **0.316.0**, installed with an explicit `--python`; the shared `.venv` was never mutated.

| Slice | Focused scope | Result |
|---|---|---|
| 1 | `tests/types/` | included in the 481-row run below |
| 2 | `tests/extensions/test_debug.py` | included in the 481-row run below |
| 1 + 2 | `/tmp/dsf-floor48/bin/python -m pytest tests/types/ tests/extensions/test_debug.py --no-cov` | 481 passed, 2 skipped |
| 3 | `/tmp/dsf-floor48/bin/python -m pytest tests/test_error_policy.py examples/fakeshop/test_query/test_error_policy_api.py --no-cov` | 48 passed |

## Deferred work catalog

- **Upstream argument rejections are masked** (this artifact, "A consequence worth stating plainly"). The fix is for the package to raise Strawberry's relay/pagination argument rejections as `GraphQLError` carrying an audited `extensions.code`, which brings them under the untouched branch of the structural rule without loosening it. Not licensed by this spec; belongs to a follow-up card.
- **The debug extension's caps are not configurable.** Deliberate ([`AGENTS.md`][agents]: add a settings key only when the feature that needs it lands, and a deployment wanting a different ceiling is a deployment running the extension in production). Revisit only if a real consumer need appears.
- **`docs/GLOSSARY.md` has no `DjangoSchema` entry**, so the constructor's two policy arguments are described only from the `ErrorPolicy` / `ResourcePolicy` side. Card `047`'s glossary rows link to a `#djangoschema` anchor that resolves to nothing. Not this card's rows; surfaced for the maintainer.
- **Card `047`'s root exports** (`ResourcePolicy`, `DjangoResourcePolicyExtension`, `DEFAULT_RESOURCE_POLICY`) are absent from the glossary's Public exports list. That card's to fix.
- **`CHANGELOG.md`** carries no `0.0.17` entry. [`AGENTS.md`][agents] reserves it and this card did not claim the permission; the release entry is the maintainer's.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[spec-048]: ../SPECS/spec-048-secure_output_defaults-0_0_17.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[plan-048]: build-048-secure_output_defaults-0_0_17.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
