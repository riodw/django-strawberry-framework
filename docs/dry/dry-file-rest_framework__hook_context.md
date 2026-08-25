# DRY review: `django_strawberry_framework/rest_framework/hook_context.py`

Status: verified

## System trace

`django_strawberry_framework/rest_framework/hook_context.py` defines immutable frozen value objects passed into consumer serializer mutation hooks ([spec-039][spec-039]).

It owns the following architectural responsibilities:

1. **Frozen Hook Execution Context:**
   - [`SerializerHookContext`][rf-hook-context] (`django_strawberry_framework/rest_framework/hook_context.py::SerializerHookContext`): Frozen slotted dataclass providing safe, immutable execution metadata to serializer hooks (`get_serializer_kwargs`, `get_serializer_injected_data`, `get_serializer_save_kwargs`).
   - Fields:
     - [`SerializerHookContext.operation`][rf-hook-context]: Declared mutation kind (`"create"` or `"update"`).
     - [`SerializerHookContext.write_alias`][rf-hook-context]: Pinned write database alias for the transaction.
     - [`SerializerHookContext.instance_pk`][rf-hook-context]: Snapshot of authorized instance primary key (or `None` on create).

2. **Frozen Upload File Metadata:**
   - [`UploadMetadata`][rf-hook-context] (`django_strawberry_framework/rest_framework/hook_context.py::UploadMetadata`): Frozen slotted dataclass standing in for stateful upload streams in hook data views.
   - Fields:
     - [`UploadMetadata.name`][rf-hook-context]: File name.
     - [`UploadMetadata.size`][rf-hook-context]: Byte size.
     - [`UploadMetadata.content_type`][rf-hook-context]: MIME type string.

Connected behavior examined:
- [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers]: Instantiates `SerializerHookContext` and `UploadMetadata` during mutation execution.
- [`django_strawberry_framework/rest_framework/sets.py`][rf-sets]: Defines base hook signatures on `SerializerMutation`.
- [`tests/rest_framework/`][tests-rf]: Verifies hook immutability, upload stream preservation, and context properties.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/rest_framework/hook_context.py --include-constants`):
- Parsed 1 target file, 57 lines.
- Inventory of symbols (8 definitions):
  - 2 classes: [`SerializerHookContext`][rf-hook-context], [`UploadMetadata`][rf-hook-context].
  - 6 attributes: [`SerializerHookContext.operation`][rf-hook-context], [`SerializerHookContext.write_alias`][rf-hook-context], [`SerializerHookContext.instance_pk`][rf-hook-context], [`UploadMetadata.name`][rf-hook-context], [`UploadMetadata.size`][rf-hook-context], [`UploadMetadata.content_type`][rf-hook-context].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `SerializerHookContext` and `UploadMetadata` are specific value objects for serializer mutation hook security. They do not mirror or duplicate logic from model mutations.

2. **Sync and async twins:**
   Zero duplication. Both dataclasses are plain frozen dataclasses shared unchanged between sync and async execution paths.

3. **Derived rather than repeated knowledge:**
   `SerializerHookContext` captures state snapshots (operation, write alias, instance pk) directly from resolver execution variables. `UploadMetadata` extracts metadata from uploaded files directly.

4. **Inverse and round-trip pairs:**
   Context and upload descriptors are instantiated once per hook call and passed down to consumer hooks.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/rest_framework/hook_context.py`][rf-hook-context], [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers], [`django_strawberry_framework/rest_framework/sets.py`][rf-sets];
   - Specifications: [`docs/SPECS/spec-039-serializer_mutation-0_0_11.md`][spec-039];
   - Test suites: [`tests/rest_framework/`][tests-rf];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding an attribute to SerializerHookContext, e.g., request_user):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/hook_context.py`][rf-hook-context] ([`SerializerHookContext`][rf-hook-context]).
  - *Propagation count:* 1 in `rest_framework/resolvers.py` (construction call).
- **Posited change 2 (Adding an attribute to UploadMetadata, e.g., charset):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/hook_context.py`][rf-hook-context] ([`UploadMetadata`][rf-hook-context]).
  - *Propagation count:* 1 in `rest_framework/resolvers.py` (construction call).

### Rejected candidates

1. **Passing live mutable model instances to hooks instead of `SerializerHookContext`:**
   - Disproved per [spec-039][spec-039]. Exposing mutable model instances creates security and state vulnerability surfaces.
2. **Passing live stream upload objects to hooks:**
   - Disproved per [spec-039][spec-039]. Consuming upload streams inside hooks exhausts the stream before serializer validation runs.

## Opportunities

None — `django_strawberry_framework/rest_framework/hook_context.py` is a clean, 57-line value-object module.

## Judgment

Verified. `rest_framework/hook_context.py` exhibits zero duplicate code and complete policy consolidation. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/hook_context.py --review docs/dry/dry-file-rest_framework__hook_context.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/rest_framework/hook_context.py`][rf-hook-context] and Worker 1's DRY review.

1. **Immutable Value Objects:**
   - Confirmed `SerializerHookContext` and `UploadMetadata` are `@dataclass(frozen=True, slots=True)` value types.
   - Confirmed fields encapsulate only necessary metadata for hook execution without exposing mutable instances or stateful file streams.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/hook_context.py --review docs/dry/dry-file-rest_framework__hook_context.md --include-constants`. 100% coverage across all definitions.

Confirmed: `django_strawberry_framework/rest_framework/hook_context.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-serializer_mutation-0_0_11.md

<!-- package source -->
[rf-hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py

<!-- tests -->
[tests-rf]: ../../tests/rest_framework/
