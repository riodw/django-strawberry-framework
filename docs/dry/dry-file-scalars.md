# DRY review: `django_strawberry_framework/scalars.py`

Status: verified

## System trace

The module owns three contracts. (1) The `BigInt` wire grammar: `_BIGINT_STRING_PATTERN`
(`^(0|-?[1-9][0-9]*)$`), the strict parser (`scalars.py::_parse_bigint`: int-excluding-bool plus
canonical decimal strings), and the strict serializer (`scalars.py::_serialize_bigint`: int-only,
canonicalized through `int.__repr__` so subclass dunders cannot forge the wire value). (2) The
package scalar registry: `BigInt = NewType(...)`, its `ScalarDefinition`, and
`scalars.py::_PACKAGE_SCALAR_MAP` — the single list of scalars the package defines;
`Upload`/`UploadDefinition` are deliberately NOT registered (Strawberry's
`DEFAULT_SCALAR_REGISTRY` already resolves them — spec-037 Decision 5). (3) The config factory
`scalars.py::strawberry_config`: merges `_PACKAGE_SCALAR_MAP` with a materialized copy of
`extra_scalar_map`, rejects collisions and a direct `scalar_map=` kwarg, forwards everything else
to `StrawberryConfig`.

Consumers traced end to end: `__init__.py` re-exports all four names (lazy); read-side typing maps
64-bit columns to `BigInt` exactly once (`types/converters.py::SCALAR_MAP`, walked by
`types/converters.py::scalar_for_field` and shared with filter inputs via
`filters/inputs.py::_scalar_from_model_field`); the three write flavors annotate file-kind inputs
with the single imported `Upload` symbol (`mutations/inputs.py::model_column_write_annotation`,
shared by mutation/form/serializer column paths; column-less arms in
`forms/inputs.py::_field_triple_and_spec` and
`rest_framework/serializer_converter.py::resolve_serializer_field`);
`management/commands/inspect_django_type.py` derives package scalar SDL names from
`_PACKAGE_SCALAR_MAP` instead of a second literal (comment documents the anti-drift intent);
fakeshop builds both real schemas through the factory (`examples/fakeshop/config/schema.py`,
`examples/fakeshop/strategy_schemas.py`). Tests: `tests/test_scalars.py` (grammar/factory units),
`tests/types/test_converters.py` (dispatch), `examples/fakeshop/apps/scalars/models.py` +
`examples/fakeshop/test_query/test_scalars_api.py` / `test_scalars_filter_api.py` (live wire),
`examples/fakeshop/tests/test_inspect_django_type.py` (name derivation). Prose: `docs/GLOSSARY.md`
`BigInt` scalar / `Upload` scalar / `strawberry_config` entries.

Lockstep surface by design: adding or renaming a package scalar moves only this module; every
other site consumes symbols or derives names.

## Verification

All five axes discharged:

1. **Cross-flavor policy mirroring** — searched `grep -rn 'Upload|BigInt|SCALAR_MAP|scalar_map'`
   across `django_strawberry_framework`. Read-side conversion is already consolidated: one
   `SCALAR_MAP`, one MRO walk (`scalar_for_field`) shared by type selection and filter inputs.
   Write-side found exactly three sites deciding "file-kind input ⇒ `Upload`": the shared
   column-backed owner plus two column-less arms (listed above). Candidate probed and REJECTED
   (see below): the symbol is single-sourced through the re-export, and the per-flavor
   finalization is a documented ownership principle, not drift.
2. **Sync and async twins** — ruled inapplicable on the target's real surface:
   `grep -c 'async def' django_strawberry_framework/scalars.py` = 0; Strawberry's scalar contract
   registers synchronous `parse_value`/`serialize` callables only
   (`scalars.py::_BIGINT_SCALAR_DEFINITION`), and no async execution path treats scalars
   differently.
3. **Derived rather than repeated knowledge** — searched `"BigInt"` literals, the regex, and
   int-subclass normalization (`int.__int__|int.__repr__|__name__` guards) outside the target.
   Code hits: `types/converters.py` maps the two field classes to the `BigInt` symbol once
   (ownership, not repetition); `inspect_django_type.py` derives names from
   `_PACKAGE_SCALAR_MAP` (explicitly anti-duplication). Near-twins examined and REJECTED:
   `utils/querysets.py::_normalized_int` repeats the base-descriptor *technique* but for a
   different rule (DB decode-path value normalization vs wire grammar; different accept-sets,
   errors, and reasons to change), and the three guarded `__name__` label helpers
   (`scalars.py::_safe_scalar_map_key_label`,
   `rest_framework/serializer_converter.py::_scalar_name`,
   `management/commands/inspect_django_type.py::_scalar_name`) share shape, not contract —
   hostile-metadata-hardened collision labels vs trusted internal diagnostics, with deliberately
   different
   fallbacks (`_safe_arg_repr` vs `repr` vs `str`); a posited change to any one message contract
   forces only its own site.
4. **Inverse and round-trip pairs** — the encode/decode halves of the BigInt grammar are
   co-located in this module and share the pattern constant plus canonical-int normalization; the
   documented accept-set asymmetry (parser also takes Python ints; serializer rejects `str`) is
   the intended input/output symmetry guard, not a twin. Searched for a second grammar half:
   `views.py` handles multipart transport→bytes without touching scalar encoding; nothing else
   parses or emits BigInt wire values. Ruled out.
5. **Contracts restated in another medium** — counted media for the BigInt contract: production
   grammar (this module), unit pins (`tests/test_scalars.py`), dispatch pins
   (`tests/types/test_converters.py`), live wire pins (`test_scalars_api.py`),
   `docs/GLOSSARY.md` prose (restates the regex and strictness rules). Docs and tests pinning a
   public contract is their job, not consolidation debt. One imprecision noted, not fixed:
   GLOSSARY says "serialized via Python `str(int_value)`" while
   `scalars.py::_serialize_bigint` deliberately uses `int.__repr__` (identical output for exact
   `int`; the prose omits the subclass-hardening reason). `docs/GLOSSARY.md` is concurrently
   dirty; left untouched.

Single-edit-site counts (posited changes):

- Add a second package scalar (e.g. a fixed-precision decimal): definition + `_PACKAGE_SCALAR_MAP`
  entry in this module only; `strawberry_config()` merges it and `inspect_django_type.py` derives
  its SDL name automatically = **1** code site.
- Rename the BigInt GraphQL name: `scalars.py::_BIGINT_SCALAR_DEFINITION` `name=` only = **1**
  (command output follows by derivation; GLOSSARY prose updates as doc duty).
- Tighten the BigInt string grammar: `_BIGINT_STRING_PATTERN` only = **1** (the serializer emits
  canonical decimal that always satisfies the pattern).
- Change a `strawberry_config` default/kwarg policy: the factory body only = **1**.
- Swap the file-input scalar for a package-custom one: **3** annotation sites + the re-export +
  spec-037 Decision 5 pins — evaluated and rejected as a consolidation target (below).

## Opportunities

None — no warranted consolidation. Every apparent multi-site candidate was disproved:

- **FILE ⇒ `Upload` stated at three build sites**
  (`mutations/inputs.py::model_column_write_annotation`, `forms/inputs.py::_field_triple_and_spec`,
  `rest_framework/serializer_converter.py::resolve_serializer_field`):
  all three reference the SAME single-sourced symbol (`from ..scalars import Upload`), so the
  realistic narrow change ("re-point which object the upload scalar is") already costs **1** edit
  in `scalars.py`; the broader change (a genuinely different upload scalar) contradicts a shipped,
  test-pinned decision (spec-037 Decision 5: re-export, ride `DEFAULT_SCALAR_REGISTRY`, identity
  asserted in `tests/test_scalars.py::test_upload_is_strawberry_builtin_re_export_not_a_wrapper`).
  Hoisting the choice into the model-less conversion tables would break those tables' documented
  contract (`annotation=None` for relation/file kinds, finalized at the build site) — a principle
  that exists because RELATION annotations genuinely vary per flavor — creating a FILE-only
  exception that couples pure kind-classification modules to a public scalar. Worse shape than the
  "duplication".
- **Base-descriptor normalization technique** (`utils/querysets.py` family vs this module): same
  idiom, different rules and failure domains; sharing a helper would couple a public wire scalar
  to queryset-internal decoding.
- **Guarded `__name__` label trio**: three diagnostics with distinct trust domains, fallbacks, and
  reasons to change; each posited message-contract change counted **1**.

The counts that came back **1** (new package scalar, scalar rename, grammar tightening, factory
policy) show the module already sits at the root owner of every rule it states.

## Judgment

`scalars.py` is already the consolidation point it should be: one grammar with both round-trip
halves co-located, one registry every consumer derives from, one factory owning merge/collision
policy, and a re-export that keeps the upload scalar single-sourced across all three write
flavors. The five-axis sweep surfaced only shape-level look-alikes whose contracts provably
diverge; recording them is the correct disposition. Zero tracked changes; pytest deferred per
AGENTS.md (not explicitly requested).

## Independent verification (Worker 2)

Hunk attribution: `git diff 3119a43 -- django_strawberry_framework/scalars.py` is EMPTY, and so is
the tree-to-tree diff `git diff 3119a43 HEAD -- <file>` — baseline snapshot, HEAD (a12c6422), and
worktree agree byte-for-byte. The maintainer's concurrent `int.__repr__` hunks referenced at
dispatch were absorbed into commit f92c1944 ("fix(relay,types,scalars): resolve the id slot and
canonical scalar form through one rule", 2026-08-25); nothing was reverted and nothing remains
uncommitted. This item added zero hunks of its own — confirmed.

Independent re-trace (all reproduced first-hand, artifact not trusted):

- Grammar single-ownership: repo-wide search for the literal pattern `(0|-?[1-9][0-9]*)` finds a
  second CODE site nowhere; every other hit is prose (CHANGELOG.md, KANBAN.md, GLOSSARY.md,
  SPECS, review/builder artifacts, this file). Parse and serialize halves are co-located here and
  share the constant; `views.py`'s multipart path is transport-only.
- FILE⇒Upload trio: read all three sites. `mutations/inputs.py:50`,
  `forms/inputs.py:59`, `rest_framework/serializer_converter.py:75` each do
  `from ..scalars import Upload`; the column-less arms annotate with that one imported object and
  the column-backed arms delegate to `model_column_write_annotation`, which returns the same
  symbol. A package-wide search for `strawberry.file_uploads` finds the import owner only in
  `scalars.py` (`_strawberry_patches.py` imports only the transport util
  `replace_placeholders_with_files`). Re-pointing which object the upload scalar IS costs 1 edit
  in this module; identity pins exist as claimed
  (`tests/test_scalars.py::test_upload_is_strawberry_builtin_re_export_not_a_wrapper`,
  `::test_strawberry_config_scalar_map_excludes_upload`). Rejection stands.
- Registry/factory single ownership: `StrawberryConfig(` is constructed only in the factory body
  inside the package; `strawberry.scalar(` is called only at
  `scalars.py::_BIGINT_SCALAR_DEFINITION` (other hits are consumer scalars in tests/examples).
  `management/commands/inspect_django_type.py:108` derives SDL names from `_PACKAGE_SCALAR_MAP`;
  the remaining `"BigInt"` string literals in package code are comments or the root `__all__`
  export pin only — no functional re-derivation a rename would force to move.
- Rejected candidates re-probed: `utils/querysets.py::_normalized_int` (`int.__int__`) sits in a
  DB-decode normalization family (`_normalized_bytearray`/`_normalized_float`/…) with different
  accept-sets and reasons to change than the wire parser — technique-sharing would couple domains;
  the label trio genuinely diverges (hostile-hardened `try/except` + `_safe_arg_repr` vs trusted
  `repr` diagnostic vs metadata-driven SDL namer). Each posited message-contract change counts 1.

Own recounts of count-of-one claims:

- Widen the wire grammar to accept a leading `+`: touches `_BIGINT_STRING_PATTERN` only. The
  str branch already converts matched strings via `int(plain_value)` (which accepts `+123`) and
  the serializer emits canonical decimal that satisfies any widened pattern = **1** code site.
- SDL rename `BigInt`→`BigInt64`: touches `name=` in `_BIGINT_SCALAR_DEFINITION` only; the
  command output follows by derivation from `definition.name`; live-query/GLOSSARY/test literals
  are contract pins (doc/test duty) = **1** code site.

Corrections noted (do not affect any count, rejection, or the verdict): the System trace says the
root package "re-exports all four names (lazy)". Actually `__init__.py:45` eagerly imports THREE
names (`BigInt`, `Upload`, `strawberry_config`); `UploadDefinition` is exported only from
`django_strawberry_framework.scalars`, and the PEP 562 lazy map covers DRF names only. The
single-sourcing substance is unaffected.

Matrix re-judged against the real surface: axis 1 searched (read side single-owned via
`SCALAR_MAP`/`scalar_for_field`, shared by `filters/inputs.py::_scalar_from_model_field` —
verified; write side three same-symbol sites); axes 2–4 ruled out with verified reasons (zero
async defs; no second grammar half; no derived-name restatement); axis 5 counted with docs/tests
correctly assigned as pinning duty, including the honestly-recorded GLOSSARY `str(int_value)`
imprecision (output-identical for exact `int`; GLOSSARY concurrently dirty, left untouched).
Verdict: **verified** — proved zero-edit stands.
