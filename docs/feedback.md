# Implementation review: spec-037 upload/file image mapping

Review target: current implementation of [`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037],
including the committed implementation range from `0273c869` through `HEAD` and
the small current working-tree tweaks in [`types/converters.py`][types-converters]
and the spec.

Verdict: **revise before handoff**. The main read/write architecture is sound:
`SCALAR_MAP` stays scalar/filter-input-only, `convert_field_output` owns the
file/image output-object branch, generated mutation inputs map file/image fields
to Strawberry's built-in `Upload`, and the tests exercise real schema execution
and temp storage. The remaining issues are narrower but still material: one
runtime edge can turn the promised empty-file `null` behavior into a GraphQL
top-level error, and a few release/process artifacts are stale enough to mislead
future maintainers.

## Findings

### P1 - Empty required file fields still produce non-null GraphQL execution errors

The parent resolver intentionally returns `None` for an empty / falsy Django
`FieldFile` at [`types/resolvers.py`][types-resolvers]::_make_file_resolver
#"return value if value else None". That is the right runtime guard. The generated
annotation, however, is nullable only when `field.null` or `field.blank` is true
at [`types/converters.py`][types-converters]::convert_field_output
#"bool(field.null or field.blank)". For a plain `models.FileField()` the SDL is
therefore `attachment: DjangoFileType!`, while the resolver can still return
`None`.

This is not just theoretical. A `FileField(blank=False, null=False)` is not a
database-level non-empty invariant; legacy rows, direct `Model.objects.create()`,
manual SQL, fixtures, or old data can still carry the empty string. In that case
the current schema turns the intended "empty / absent file resolves to null"
contract into `Cannot return null for non-nullable field ...` and nulls the
containing response.

Recommended fix: make generated file/image output nullable by default whenever
the generated parent resolver can return `None`. In practice that means
`FileField` / `ImageField` read output should default to `DjangoFileType | None`
/ `DjangoImageType | None` regardless of `blank`, with `Meta.required_overrides`
as the explicit opt-in for callers who want to assert a stronger invariant. Add a
schema-execution test for a required `FileField` with an empty stored value.

### P1 - The final build artifact breaks diff checks while claiming they pass

`git diff --check 0273c869..HEAD` reports a conflict-marker-style line in
[`docs/builder/bld-final.md`][builder-final] #"======= 1 failed, 2212 passed".
The line is a pytest summary inside a fenced block, not a real merge conflict,
but Git still flags any line beginning with that marker shape. The same artifact
later records `git diff --check` as **PASS**, so the release transcript is now
self-contradictory under the implementation range.

Recommended fix: rewrite that transcript line so it does not begin with seven
equals signs, for example `pytest summary: 1 failed, ...`, then re-run the same
diff check over the review range and update the artifact truthfully.

### P2 - The DONE card still carries in-progress planning state

The 037 card was moved under `## Done`, but [`KANBAN.md`][kanban]
#"DONE-037-0.0.11 - Upload scalar and file / image field mapping" still says
`Status: In progress` and `Planning note: planned`. That leaves the project
source of truth internally inconsistent: the card id and board column say DONE,
while the card body says it is still active.

Recommended fix: update the kanban database fields that render those card-body
values, then re-render `KANBAN.md` / `KANBAN.html` instead of hand-editing the
rendered markdown. If the same stale `planningState` pattern is intentionally
left on older DONE cards, record that as a deliberate board convention; otherwise
clean 036 at the same time.

### P2 - Shipped source and tests still carry `TODO-ALPHA-037` anchors

The implementation removed the staged `NotImplementedError`, but shipped files
still contain `TODO-ALPHA-037-0.0.11` wording in durable comments/docstrings, for
example [`scalars.py`][scalars] #"TODO-ALPHA-037-0.0.11",
[`mutations/inputs.py`][mutation-inputs] #"TODO-ALPHA-037-0.0.11 lifted", and the
new tests. Per [`AGENTS.md`][agents], staged source-site TODO anchors are removed
in the same change that ships the slice. Keeping the active TODO id in shipped
source makes future sweeps noisy and makes the DONE card look unfinished.

Recommended fix: replace shipped-code anchors with non-TODO provenance such as
`spec-037` / `DONE-037` where historical context is useful, and remove the rest.
The new builder sweep added in [`docs/builder/BUILD.md`][builder-build] only
searches `TODO(spec-<NNN>)`; it should also catch card-id anchors if those are
used for staging.

### P3 - An unrelated orders test correction is bundled into the 037 range

[`tests/orders/test_sets.py`][test-orders] #"OrderSet could not resolve" changes
an orders/permissions assertion, while no orders production file changed in the
037 implementation range. [`docs/builder/bld-final.md`][builder-final] records
this as an out-of-scope maintainer-authorized re-pin, not part of the upload/file
feature.

Recommended fix: split that one-line test correction into its own commit or
explicitly document in the final handoff that the 037 commit contains an
unrelated baseline test repair. The production helper was already correct; this
should not be hidden inside the upload mapping change.

## Checks run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-037-upload_file_image_mapping-0_0_11.md`
  passed.
- `git diff --check 0273c869..HEAD` failed on the builder transcript line noted
  above.
- Lightweight `uv run python -c ...` probes confirmed `Upload` resolves under
  plain `StrawberryConfig` and `strawberry_config()`, and confirmed the required
  empty-file output edge currently raises a non-null GraphQL error.
- `uv run python scripts/check_trailing_commas.py --check` failed only under
  `.claude/worktrees/...`; I treated that as out-of-scope for this review.
- I did **not** run pytest.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[kanban]: ../KANBAN.md

<!-- docs/ -->
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[builder-build]: builder/BUILD.md
[builder-final]: builder/bld-final.md

<!-- django_strawberry_framework/ -->
[mutation-inputs]: ../django_strawberry_framework/mutations/inputs.py
[scalars]: ../django_strawberry_framework/scalars.py
[types-converters]: ../django_strawberry_framework/types/converters.py
[types-resolvers]: ../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-orders]: ../tests/orders/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
