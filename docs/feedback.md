# Review - spec-032 Full Relay build plan, revision 2

Reviewed the updated `docs/spec-032-full_relay-0_0_9.md` against the current
source and the shipped `spec-030` / `spec-031` contracts. The three prior
findings are fixed in the spec: stale offset cursors are now no-error only,
secondary model-label helper asymmetry is documented, and root fields are
nullable-by-contract.

## Findings

### P2 - Revision 2 cites a mutable feedback file that this task replaces

`docs/spec-032-full_relay-0_0_9.md::Revision history` now says the first review
was "captured in `docs/feedback.md`" and several normative sections cite
`docs/feedback.md P1/P2`. But `docs/feedback.md` is a reusable review target;
this review replaces it. After this pass, those citations no longer point at
the first review or at the P1/P2 text they describe.

That makes the standing spec depend on a mutable scratch artifact. The revision
history already contains the substance of the first review, so the simplest fix
is to remove the `docs/feedback.md P1/P2` citations from normative sections and
cite only the spec decisions / revision text. If an external review artifact is
wanted, archive the first review under a stable path and link to that instead.

### P2 - Explicit `relation_shapes` entries can be silently ignored on consumer-authored relations

`docs/spec-032-full_relay-0_0_9.md::Decision 6` says consumer-overridden
relations are skipped entirely, while Decision 7 validates unknown,
non-relation, single-valued, excluded, and non-Relay cases. It does not say what
happens when `Meta.relation_shapes` explicitly names a relation that the
consumer also overrides with an annotation or `strawberry.field`.

Under the current wording, `relation_shapes = {"books": "connection"}` on a
consumer-authored `books` relation would be accepted and then skipped, so the
explicit request neither adds `booksConnection` nor suppresses the list field.
That violates the spec's explicit-request fail-loud posture for non-Node targets
and name collisions.

Add a validation rule: an explicit `relation_shapes` key that names a
consumer-authored relation raises `ConfigurationError` explaining that consumer
overrides own the field shape. Keep the default `"both"` upgrade skip for
consumer-authored relations, since that preserves existing override behavior.

### P3 - Relation connection collision checks need to cover GraphQL names, not only Python attrs

Decision 6 and the Test plan require a collision error when `<field>_connection`
already exists as a model field or consumer attribute. That catches Python-name
collisions, but the public field name is produced through Strawberry's name
converter. With default camel-casing, a consumer-authored `booksConnection`
attribute can collide in SDL with the generated `books_connection` field even
though the Python attribute name is different. Similar collisions are possible
with custom `name_converter` / `auto_camel_case` settings.

The spec should require a GraphQL-surface collision check, using the same naming
rule Strawberry will apply for the schema config, or at least pin the default
camel-case collision case in tests. Otherwise the build can pass the documented
Python-name check but still fail later with an opaque schema collision.

## Checks run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md`
  -> `OK: 38 terms`.
- No pytest run per repo instructions.
