# Feedback: spec-029 TODO-scaffold verification

## Verdict

The spec is broadly implementable and the TODO scaffold mapped to real source sites without exposing a major design mismatch. It is also clearly aligned with the package direction: DRF-style `Meta` surfaces, real fakeshop acceptance coverage, and parity-enabling foundation work rather than Strawberry-decorator API drift.

That said, scaffolding exposed several places where the spec should be tightened before implementation so the slice work does not become order-dependent or accidentally ship an awkward interim surface.

## Findings

### P1 — The `--schema` cold-path test is not cold if `config.schema` is already cached

The spec says the cold-path test should start from `registry.clear()` and call `call_command("inspect_django_type", "BookType", "--schema", "config.schema")` without the reload fixture. In an in-process pytest run, that is not enough. If `config.schema` or app schema modules are already in `sys.modules`, `import_module_symbol("config.schema", default_symbol_name="schema")` can return the cached schema symbol without re-running class registration or `finalize_django_types()`. After `registry.clear()`, that leaves an empty registry and makes the test order-dependent.

Clarify the test plan: either run the cold-path assertion in a subprocess management-command invocation, or explicitly evict/reload the relevant schema modules before calling `call_command`. The production command should still only import `--schema`; the test harness must simulate a real cold CLI process.

### P1 — New management-command file must fail loudly until implemented

The spec tells implementers to create `django_strawberry_framework/management/commands/inspect_django_type.py`. Once that file exists, Django command discovery will load it. A comment-only or TODO-only file produces an unhelpful `AttributeError` because Django expects a `Command` class.

Add an implementation note: if the file lands before the real command body, it must define a minimal `Command(BaseCommand)` whose `handle()` raises `CommandError` naming spec-029 Slice 2. Better yet, do not create the command file until the command is implemented. This keeps interim branches fail-loud and grep-stable.

### P2 — The placeholder-command behavior should not count as Slice 2 completion

Related to the previous point: a fail-loud `Command` shell is useful as a TODO anchor, but it is not the shipped command. The Definition of Done should explicitly require successful `call_command` happy-path output and failure-mode coverage, not merely command discovery or `manage.py help` working.

Suggested clarification: `manage.py help inspect_django_type` may work before implementation, but Slice 2 is incomplete until `handle()` resolves types, reads finalized definitions, and prints the field table.

### P2 — The inspect-command pseudocode needs to name the Relay-suppressed pk case everywhere implementation guidance appears

The Decision text covers the Relay-suppressed primary key: Relay `Node` types omit the pk from `origin.__annotations__`, and the command must report the interface-provided `GlobalID!` row instead of indexing annotations. The TODO scaffold needed this called out explicitly because the naive pseudocode naturally says “read rows from `origin.__annotations__`.”

Make sure all implementation-plan and command-pseudocode references include that exception, not only Decision 4 and the test plan. Otherwise the implementation path is likely to reintroduce the `KeyError` the spec already diagnosed.

### P2 — The Slice 3 validation helper needs a precise selected-name vs model-field split

The spec correctly requires rejecting unknown, excluded, consumer-authored, relation, and Relay-suppressed pk override targets. The implementation guidance should be more explicit about deriving two different sets:

- model field names from `model._meta.get_fields()` for unknown-field reporting
- selected field names from the post-`Meta.fields` / `Meta.exclude` result for excluded/not-selected reporting

Without that split, an implementer can collapse unknown and excluded fields into one error path, weakening the `Meta.exclude` contract the spec explicitly cares about.

### P2 — The `required_overrides` acceptance resolver should specify ordering

The spec correctly says the resolver must use `Book.objects.exclude(subtitle__isnull=True)` so `subtitle: String!` does not violate runtime data. It should also require deterministic ordering, likely `.order_by("id")`, because the existing live HTTP tests generally expect stable response ordering.

This is not a design blocker, but it prevents flaky acceptance assertions once the data-query test selects rows.

### P2 — Slice 1’s “every extensions entry” audit should include a mechanical post-migration gate

The spec says to audit with `rg 'extensions=\['` and migrate every anonymous, named, strictness, bare class, and subclass-instance entry. Add a post-migration gate that searches for the forbidden forms specifically:

- `extensions=[DjangoOptimizerExtension()]`
- `extensions=[DjangoOptimizerExtension]`
- `extensions=[ext]`
- `extensions=[_CaptureExt()]`
- `lambda: DjangoOptimizerExtension()`

The broad `extensions=[` audit finds construction sites, but the forbidden-form grep catches the exact regressions Slice 1 is trying to remove.

### P3 — The docs/TREE update should be explicitly delayed until the command is real

The spec currently lists `docs/TREE.md` in Slice 2 doc updates. That is right once the command exists as a shipped module. If a TODO-only scaffold file exists temporarily, `TREE.md` should not describe it as shipped command behavior.

Clarify that `TREE.md` is updated in the Slice 2 implementation commit, not in a planning scaffold, unless the wording clearly says “planned placeholder.”

### P3 — CHANGELOG permission is clear, but placeholder TODOs should not imply release-note content exists

The spec properly grants per-slice CHANGELOG edit permission. Add a small note that TODO scaffolding must not add real `[Unreleased]` bullets until the slice ships. A TODO comment under `[Unreleased]` is acceptable as a temporary anchor, but it must not be confused with shipped release-note content.

### P3 — The spec’s scaffold guidance could explicitly mention `ERA001`

The repo has `ERA001` enabled, and TODO pseudocode in Python files can trigger commented-out-code lint. The implementation guidance should say TODO pseudocode in Python source either needs to be prose-shaped or carry targeted `# noqa: ERA001` on lines Ruff flags.

This is a process clarification, not a product-design issue, but it prevents a predictable lint churn during scaffold or staged implementation work.
