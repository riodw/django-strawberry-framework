# Spec: Secure output and error defaults — drop the filesystem path, fail the debug extension closed, mask production errors

Targeted at `0.0.14` (card [`DONE-048-0.0.14`][kanban]). This is **card 3 of the
four-card security-remediation program** derived from the hardening audit in
[`docs/feedback2.md`][feedback2]; it closes that audit's **S5** (generated file output
exposes absolute server paths), **S8** (the debug extension does not fail closed under
`DEBUG=False`), and **S10** (production exception masking remains opt-in). It follows
[`spec-046`][spec-046] (transport security) and [`spec-047`][spec-047] (the execution
resource policy); card [`WIP-ALPHA-049-0.0.14`][kanban] (dependency / CI hygiene) closes
the program.

Deliberation, rejected alternatives, and this spec's change record live in its companion
[`spec-048-secure_output_defaults-0_0_14-rationale.md`][rationale].

**`docs/feedback2.md` is review evidence this spec references, not a substitute for it.**
The audit established the facts; every decision, default, public-API shape, compatibility
promise, and test row below is this spec's own.

**This card contains an intentional, documented alpha breaking change**
([Decision 4](#decision-4--the-break-is-justified-and-carries-a-one-line-migration)): the
`path` field disappears from every generated file and image output in the default schema.
The package's documented API freeze begins at `1.0.0`, and cards 046 and 047 both set the
precedent that correcting a confirmed security-boundary default during alpha outranks
migration convenience.

Status: **SHIPPED — all five slices are built and released.** The `Status:` line is the
completion source of truth (the shipped-spec convention); the Slice checklist boxes below
stay unticked. `CHANGELOG.md` carries no `0.0.14` entry — [`AGENTS.md`][agents] reserves
that entry for the maintainer.

**Version boundary** (see
[Decision 12](#decision-12--the-version-bump-belongs-to-the-0014-joint-cut)):
this card targets `0.0.14`, which the version quintet already reads, so its Slice 5 owns
the documentation fold-in and no part of the quintet.

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits without explicit
permission. This card's Slice 5 does **not** claim that permission — the release entry is
the maintainer's.

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`DjangoFileType`][glossary-djangofiletype], [`DjangoImageType`][glossary-djangoimagetype]
  — the generated file/image output objects whose default field set loses `path`.
- [Specialized scalar conversions][glossary-specialized-scalar-conversions],
  [Scalar field conversion][glossary-scalar-field-conversion] — the conversion surface that
  picks which of those objects a `FileField` / `ImageField` column renders as.
- [`Upload` scalar][glossary-upload-scalar] — the write-side counterpart; unchanged here,
  named so the two halves of the file surface are not confused.
- [`DjangoType`][glossary-djangotype], [`Meta.model`][glossary-metamodel],
  [`Meta.fields`][glossary-metafields], [`Meta.exclude`][glossary-metaexclude] — the type
  declaration the new opt-in key joins.
- [`Meta.nullable_overrides`][glossary-metanullable_overrides],
  [`Meta.required_overrides`][glossary-metarequired_overrides] — the exact validation
  precedent the new `Meta` key copies, field for field.
- [`ConfigurationError`][glossary-configurationerror] — the typed build-time failure for an
  invalid opt-in target.
- [Relation handling][glossary-relation-handling],
  [Definition-order independence][glossary-definition-order-independence],
  [`finalize_django_types`][glossary-finalize_django_types] — the build pipeline the
  opt-in threads through.
- [`DjangoDebugExtension`][glossary-djangodebugextension],
  [Developer-only debug posture][glossary-developer-only-debug-posture],
  [Debug payload availability][glossary-debug-payload-availability],
  [Debug SQL row][glossary-debug-sql-row],
  [Debug exception row][glossary-debug-exception-row],
  [Django debug-cursor capture][glossary-django-debug-cursor-capture],
  [Reference-counted cursor coordinator][glossary-reference-counted-cursor-coordinator],
  [Bounded query-log rollover][glossary-bounded-query-log-rollover],
  [Async SQL-capture boundary][glossary-async-sql-capture-boundary] — the diagnostic
  subsystem that gains a gate and a set of caps.
- [Masking-extension ordering][glossary-masking-extension-ordering] — the existing rule
  that the debug extension must tear down before any masking extension; the new error
  policy has to obey it from the other side.
- [Response-extension merge semantics][glossary-response-extension-merge-semantics],
  [Response-extensions debug middleware][glossary-response-extensions-debug-middleware],
  [Debug-toolbar middleware][glossary-debug-toolbar-middleware],
  [Graphene debug migration][glossary-graphene-debug-migration] — the consumers of the
  debug payload whose contract the caps must not break.
- [Strawberry extension lifecycle][glossary-strawberry-extension-lifecycle],
  [Per-operation extension isolation][glossary-per-operation-extension-isolation] — the
  construction and per-request semantics both new gates depend on.
- [Execution resource policy][glossary-execution-resource-policy],
  [`ResourcePolicy`][glossary-resourcepolicy],
  [`DjangoResourcePolicyExtension`][glossary-djangoresourcepolicyextension] — the
  policy-object precedent this card copies for errors, down to the settings key shape and
  the auto-install seam.
- [`FieldError` envelope][glossary-fielderror-envelope] — the validation surface that is
  `data`, not `errors`, and is therefore untouched by masking.
- [Per-field permission hooks][glossary-per-field-permission-hooks],
  [`SerializerMutation`][glossary-serializermutation],
  [`DjangoMutation`][glossary-djangomutation],
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] — the write surfaces whose
  deliberate rejections must survive the mask.
- [`SyncMisuseError`][glossary-syncmisuseerror] — the multiple-inheritance precedent for a
  package error that is also a `GraphQLError`.
- [`request_from_info`][glossary-request_from_info] — the info-to-request seam the
  extension reuses rather than re-deriving.
- [`TestClient`][glossary-testclient], [Probe URLconf][glossary-probe-urlconf],
  [`seed_data`][glossary-seed_data],
  [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the test tiers and
  disciplines that decide where each regression lives.
- [Joint version cut][glossary-joint-version-cut] — the release rule this card is
  explicitly NOT subject to.
- [Schema audit][glossary-schema-audit] — the build-time surface audit whose failure
  vocabulary the new `Meta` key's rejections match.

Terms this spec ADDED to the glossary in Slice 5:
[`Meta.filesystem_path_fields`][glossary-metafilesystem_path_fields] (the opt-in key),
[`DjangoFilePathType`][glossary-djangofilepathtype] and
[`DjangoImagePathType`][glossary-djangoimagepathtype] (the two opt-in output types),
[`ErrorPolicy`][glossary-errorpolicy] (the policy object),
[`DjangoErrorPolicyExtension`][glossary-djangoerrorpolicyextension] (the masking
extension), and a fail-closed-gate paragraph folded into the existing
[`DjangoDebugExtension`][glossary-djangodebugextension] and
[Developer-only debug posture][glossary-developer-only-debug-posture] entries.

## Slice checklist

Each top-level item maps to one commit / PR.

- [ ] **Slice 1 — the safe file default and its opt-in**
      `types/converters.py`: `path` leaves [`DjangoFileType`][glossary-djangofiletype] /
      [`DjangoImageType`][glossary-djangoimagetype] for a private
      `_FileSystemPathFields` mixin, composed into two new public
      `DjangoFilePathType` / `DjangoImagePathType`; `convert_field_output` grows
      `expose_filesystem_path=`. `types/base.py`: the `Meta.filesystem_path_fields`
      snapshot, its validation, and the frozenset threaded into `_build_annotations`.
- [ ] **Slice 2 — the debug extension fails closed and bounds its payload**
      `extensions/debug.py`: the `__init__` it lacks, the `allow_unsafe_production`
      acknowledgement, the `settings.DEBUG` gate that makes the extension inert, the one
      warning, and the six module-level payload caps behind one shared truncation helper.
- [ ] **Slice 3 — the production error policy**
      `error_policy.py` (new: `ErrorPolicy`, `DEFAULT_ERROR_POLICY`,
      `resolve_error_policy`), `conf.py::error_policy_setting()` and `ERROR_POLICY_KEY`,
      `extensions/error_policy.py::DjangoErrorPolicyExtension`, and the
      `DjangoSchema(error_policy=…)` resolution plus the prepend install.
- [ ] **Slice 4 — tests across the three trees**
      Live rows in `examples/fakeshop/test_query/`, package rows in `tests/`, and the
      per-app rows the SDL and settings-override probes need.
- [ ] **Slice 5 — docs fold-in**
      `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`,
      and `KANBAN.md`. The version quintet is the joint cut's, not this slice's.

## Problem statement

Three independent defaults each hand a client information the client was never meant to
have, and each of the three is safe only because someone remembered something.

**S5 — every generated file output publishes an absolute server path.**
`types/converters.py::DjangoFileType.path` returns `FieldFile.path`, and its own field
description calls it "the absolute filesystem path".
[`DjangoImageType`][glossary-djangoimagetype] subclasses the type and inherits it. So every
`FileField` and `ImageField` column on every [`DjangoType`][glossary-djangotype] in every
schema this package generates offers `path: String` to any client that can reach the row —
whenever the storage backend supports one. An SDL probe found four such occurrences in the
example project alone. Row visibility still governs *which* file-bearing object a client
can reach, but an absolute deployment path is unnecessary metadata on top of that: it
leaks usernames, release directory names, container mount points, tenant layout, and
storage conventions, and it is exactly the material that turns a later traversal, template,
or logging defect into an exploitable one. The stored `name` can also expose a storage key,
but `name` is frequently application data a client legitimately renders, so it does not
justify the same unconditional removal — its sensitivity is documented instead.

**S8 — the diagnostic extension is armed in production by a single list entry.**
`extensions/debug.py::DjangoDebugExtension` publishes interpolated SQL parameter values,
exception types, exception messages, and tracebacks carrying server paths. Its docstring
warns, correctly and at length, never to enable it on an internet-facing schema. The
implementation, deliberately, does not consult `settings.DEBUG` at all — and it has no
`__init__`, so there is no place a deployment could state an intent. One entry in a
production schema's `extensions=[…]` list silently turns the disclosure on, and the
response containing it is routinely copied into logs, tickets, and error trackers.
Documentation is not a sufficient guard for a response feature whose entire purpose is to
publish secrets. Separately, the payload is unbounded: a large operation's query log and
exception chain amplify into an enormous response with no ceiling of any kind.

**S10 — an unexpected exception's literal message reaches the client.** This is
graphql-core's documented behavior and `SECURITY.md` says so: unhandled resolver and hook
exceptions are returned verbatim unless the consumer installs Strawberry's `MaskErrors` or
overrides `Schema.process_errors`. A focused probe confirmed that
`ValueError("internal tenant secret /srv/private")` raised inside a resolver arrives at the
client with that message intact. It is not an undisclosed vulnerability; it is a weak
default for the package's *required* schema class.
[`DjangoSchema`][glossary-execution-resource-policy] already centralizes mutation
integrity and — since the resource-policy card ([`spec-047`][spec-047]) — the execution
resource policy, so it is precisely the
place a production error policy belongs. A production deployment should not become unsafe
by forgetting one Strawberry extension.

The three share one root cause: **the safe behavior was available but optional, and the
default was the unsafe one.** In each case the correction is to move the safe behavior into
the default and make the unsafe behavior an explicit, auditable, per-schema declaration.

## Current state

Shipped before this card:

- `types/converters.py` ships [`DjangoFileType`][glossary-djangofiletype] with
  `name` / `size` / `url` / `path` and [`DjangoImageType`][glossary-djangoimagetype] adding
  `width` / `height`. `_safe_file_attr` guards every storage-backed attribute with a narrow
  `(ValueError, OSError, NotImplementedError)` catch, deliberately letting
  `SuspiciousFileOperation` propagate; `name` is read directly.
- `types/base.py` validates [`Meta.nullable_overrides`][glossary-metanullable_overrides]
  and [`Meta.required_overrides`][glossary-metarequired_overrides] in the `_ValidatedMeta`
  snapshot and threads both as frozensets into `_build_annotations`.
- `extensions/debug.py` ships [`DjangoDebugExtension`][glossary-djangodebugextension] with
  no `__init__`, one synchronous `on_operation` generator serving both execution colors, a
  [reference-counted cursor coordinator][glossary-reference-counted-cursor-coordinator],
  and an idempotent `get_results`.
- `schema.py::DjangoSchema` resolves the [`ResourcePolicy`][glossary-resourcepolicy] once at
  construction and installs
  [`DjangoResourcePolicyExtension`][glossary-djangoresourcepolicyextension] by APPENDING it
  through `_with_resource_policy_extension`.
- `resource_policy.py` + `conf.py::resource_policy_setting()` are the shipped shape for
  "one frozen policy dataclass, one thin settings reader, one resolve function with a
  three-level precedence ladder".
- Every framework-owned client rejection is already raised as a `graphql.GraphQLError` —
  the GlobalID rejections, `ResourceLimitExceeded`, the connection / keyset / filter
  rejections, and `mutations/resolvers.py`'s permission denial.

Not shipped, and what this card adds: any way to keep a filesystem path out of a generated
schema; any way to ask for one deliberately; any `settings.DEBUG` awareness in the debug
extension; any bound on the debug payload; and any package-owned production error policy.

## Goals

1. **The default output is safe.** A schema built with no security-specific configuration
   publishes no absolute filesystem path, no diagnostic payload under `DEBUG=False`, and no
   unexpected exception's literal message.
2. **Every unsafe behavior remains reachable, but only by an explicit, auditable, local
   declaration** — a `Meta` key on the type, a constructor argument on the extension, a
   schema argument on `DjangoSchema`. Never a global flag that re-arms every schema in the
   process.
3. **Deliberate client-facing errors keep their contract.** Parse errors, validation
   errors, [`FieldError` envelopes][glossary-fielderror-envelope], and every audited
   framework `GraphQLError` code survive the mask untouched.
4. **Fail closed, not fail loud.** A diagnostics misconfiguration must not become an
   outage; a masking policy must not become a way to hide a field's identity.
5. **One implementation per behavior**, shared by sync and async, by both WebSocket
   protocols, and by every transport — because each is a `SchemaExtension` hook or a
   type-construction decision, not a per-transport branch.
6. **The correlation identifier is the contract.** What reaches the client must be enough
   to find the exception in the log and nothing more.

## Non-goals

- **Removing `name` from the default file output.** `name` can expose a storage key, but it
  is regularly the value an application renders. Its sensitivity is documented in
  [`docs/GLOSSARY.md`][glossary]; it is not removed.
- **A general PII or field-level redaction framework.** This card removes one field that is
  never client data. A declarative "sensitive field" vocabulary is a much larger surface
  with its own directive and introspection questions.
- **Structured / JSON logging.** The correlation id goes to the package logger at `ERROR`
  with `exc_info`; how a deployment formats, ships, or indexes that record is the
  deployment's concern.
- **Error reporting integrations** (Sentry and friends). A consumer's own extension or
  logging handler already receives the exception; the package does not grow a vendor seam.
- **Rate-limiting or throttling the error path.** A masked error still logs; log volume is a
  deployment concern, tracked in
  [Risks and open questions](#risks-and-open-questions).
- **Bounding the debug payload by wall-clock or query time.** The caps here are structural
  (rows and characters), which is what the audit's evidence names.

## Borrowing posture

`strawberry-graphql-django` ships `DjangoFileType` with `name` / `path` / `size` / `url`
and `DjangoImageType` adding `width` / `height`; this package's shape was copied from it.
Continuing to copy it is exactly the finding: an upstream default is not a security
argument, and this package's whole positioning is that a Django-shaped default should be a
*safe* Django-shaped default. `graphene-django` exposes no structured file type at all, so
[Single-upstream parity][glossary-single-upstream-parity] already makes the field optional
rather than foundational. **The divergence is deliberate and is stated in the glossary
entry**, so a reader migrating from either upstream finds it rather than discovering it.

`graphene-django`'s `DjangoDebug` has no `DEBUG` gate either. Neither upstream ships a
production error policy; Strawberry ships `MaskErrors` as an optional extension.

What is borrowed:

- **The mechanism.** Both new behaviors are `SchemaExtension` hooks, and the error policy's
  replacement error is an ordinary `GraphQLError`. That is what buys transport parity for
  free — every transport already renders a `GraphQLError`.
- **`MaskErrors`' idea** that masking belongs in an `on_operation` teardown that rewrites
  `result.errors`.
- **The `ErrorPolicy` object's shape**, borrowed from this package's own
  [`ResourcePolicy`][glossary-resourcepolicy] rather than from an upstream: a frozen
  dataclass, a `resolve_*` function with a three-level precedence ladder, a thin `conf.py`
  reader, and a `DjangoSchema` argument resolved once at construction.

What is deliberately **not** borrowed: `MaskErrors`' all-or-nothing default predicate and
its silence, `Schema.process_errors` as the masking seam, and upstream's `path` field.
Why each was declined is in the [rationale][rationale].

## User-facing API

### Opting a column back into a filesystem path

```python
class DocumentType(DjangoType):
    class Meta:
        model = Document
        fields = ("id", "title", "attachment")
        # Loud, per-field, per-type. The generated `attachment` field becomes
        # `DjangoFilePathType` (or `DjangoImagePathType` for an ImageField),
        # which is `DjangoFileType` plus a `path` carrying a security warning
        # in its own field description.
        filesystem_path_fields = ("attachment",)
```

Accepted values are a `tuple`, `list`, `set`, or `frozenset` of column names selected by
[`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]. Anything else
— an unknown name, a name the type does not select, a column whose annotation or
`strawberry.field` the consumer already owns, or a non-file column (a relation target
included) — raises [`ConfigurationError`][glossary-configurationerror] naming the offending
field at type-construction time.

The resulting SDL:

```graphql
type DocumentType implements Node {
  id: GlobalID!
  title: String!
  attachment: DjangoFilePathType
}

type DjangoFilePathType {
  name: String!
  size: Int
  url: String
  """
  SECURITY: the absolute filesystem path on the server. Opted into by
  Meta.filesystem_path_fields. Do not expose to untrusted clients.
  """
  path: String
}
```

A schema that does not opt in emits `DjangoFileType` / `DjangoImageType`, which carry no
`path` field at all — not a nullable one, not a permission-guarded one. The field does not
exist in the SDL.

### Running the debug extension where `DEBUG` is false

```python
schema = DjangoSchema(
    query=Query,
    extensions=[
        # Default (and the only spelling most schemas should ever use): the
        # bare class. Inert whenever settings.DEBUG is false.
        DjangoDebugExtension,
    ],
)

controlled_diagnostic_schema = DjangoSchema(
    query=Query,
    extensions=[
        # The explicit acknowledgement. A factory, not an instance, so the
        # fresh-per-operation contract still holds.
        lambda: DjangoDebugExtension(allow_unsafe_production=True),
    ],
)
```

### The production error policy

```python
from django_strawberry_framework import DjangoSchema, ErrorPolicy

schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    error_policy=ErrorPolicy(message="Something went wrong. Please contact support."),
)
```

`error_policy=` also accepts a plain mapping applied over the package defaults, and
`error_policy={"enabled": False}` is the explicit opt-out.

```python
DJANGO_STRAWBERRY_FRAMEWORK = {
    "ERROR_POLICY": {
        "message": "An unexpected error occurred.",
        "correlation_extension_key": "correlationId",
    },
}
```

Precedence, highest first: the `DjangoSchema(error_policy=…)` argument, the setting, the
package defaults. The resolved policy is exposed as `schema.error_policy`.

### The masked error on the wire

```json
{
  "data": {
    "expensiveReport": null
  },
  "errors": [
    {
      "message": "An unexpected error occurred.",
      "path": [
        "expensiveReport"
      ],
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ],
      "extensions": {
        "correlationId": "9f2c41a07b1e4d5c8a3f6b2d0e7c15a4"
      }
    }
  ]
}
```

The matching server-side log record, at `ERROR` on the `django_strawberry_framework`
logger, carries the correlation id in its message text and the original exception as
`exc_info`.

## Architectural decisions

### Decision 1 — `path` leaves the safe default for two composed opt-in types

`types/converters.py` keeps [`DjangoFileType`][glossary-djangofiletype] with `name`
(non-null) / `size` / `url`, and [`DjangoImageType`][glossary-djangoimagetype] subclassing
it with `width` / `height`. The single `path` resolver moves to a private
`@strawberry.type`-decorated mixin, `_FileSystemPathFields`, and two new **public** output
types compose it:

```python
class DjangoFilePathType(DjangoFileType, _FileSystemPathFields): ...
class DjangoImagePathType(DjangoImageType, _FileSystemPathFields): ...
```

Four properties follow, and each is load-bearing:

- **The field is gone from the SDL, not merely null.** A field that exists and always
  answers `null` still tells a client the concept exists, still appears in introspection,
  and is one line of "temporary" code away from answering. Absence is the only honest
  removal.
- **One `path` definition, not two.** The mixin means the resolver, its narrow storage
  guard, and its security description exist once. Two copies of a security-sensitive
  resolver drift, and the drift is silent.
- **The description is the warning.** The `path` field's own description states, in the
  SDL a consumer generates and reads, that this is the absolute filesystem path on the
  server and that it was opted into. The warning travels with the field.
- **The opt-in types subclass the safe ones in PYTHON**, so the shared members —
  `name` / `size` / `url`, plus `width` / `height` on the image pair — have exactly one
  definition and one set of resolvers, and a later improvement to the file surface reaches
  the opt-in shapes for free. This is a source-level property and nothing more: in the SDL
  the four types are four unrelated GraphQL objects, so a fragment whose type condition
  names `DjangoFileType` does **not** match a field typed `DjangoFilePathType`. That is
  what the migration note in
  [Decision 4](#decision-4--the-break-is-justified-and-carries-a-one-line-migration) means
  by "a client whose query names the type in a fragment condition updates that name";
  Python inheritance is not GraphQL subtyping, and only an `interface` would be.

*Alternatives rejected: see the [rationale][rationale] (deleting `path` entirely, a
nullable always-`None` `path`, a global settings flag, a permission class on the field).*

### Decision 2 — The opt-in is a per-field `Meta` key, validated exactly like the override sets

`Meta.filesystem_path_fields` is a `tuple` / `list` / `set` / `frozenset` of column names on a
[`DjangoType`][glossary-djangotype]. The card leaves the opt-in shape open ("Meta key vs
server-only field"); the spec picks the `Meta` key, because the `Meta` class is this
package's entire consumer surface and a security decision belongs where a reviewer already
looks.

Threading mirrors [`Meta.nullable_overrides`][glossary-metanullable_overrides] and
[`Meta.required_overrides`][glossary-metarequired_overrides] field for field:

1. The `_ValidatedMeta` snapshot normalizes the declaration into a `frozenset[str]` through
   the same `_normalize_sequence_spec` helper both override sets use. That helper accepts
   any non-string `Sequence` **or** `Set` — every key routed through it names an unordered
   set of field names, and three of the four normalize to a `frozenset` on the next line, so
   refusing the literal a consumer would write for a set would be a shape gate contradicting
   its own semantics. A `str` stays refused (it is iterable, so one field name would be read
   as a sequence of single-character names). The helper takes the key's NAME and puts it in
   the rejection message, so a mistyped `filesystem_path_fields` is not reported against
   `Meta.exclude`.
2. The same validation pass that rejects an illegal override target rejects an illegal
   path target, with four named failures, each raising
   [`ConfigurationError`][glossary-configurationerror] naming the offending field: **unknown
   name** (no such model field), **non-selected name** (excluded by
   [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude]),
   **consumer-authored column** (a consumer annotation or `strawberry.field` already owns
   that field's output type, so the opt-in could not take effect), and **non-file column**
   (any selected field whose output type is not a file/image object — which is how a
   relation target is refused too, since a `ForeignKey` / M2M has no file to publish).
   The first two reuse `_selected_meta_targets`, so their consumer-visible shape matches
   every other `Meta.*` target key; the last two are this key's own domain checks.
3. The frozenset threads into `types/base.py::_build_annotations` and on into
   `types/converters.py::convert_field_output(..., expose_filesystem_path=...)`, whose only
   job is to pick the path-bearing sibling type from a single mapping
   (`DjangoImageType -> DjangoImagePathType`, `DjangoFileType -> DjangoFilePathType`).

**Reusing the override-set precedent is not stylistic.** It means there is one place a new
`Meta` key's normalization lives, one place its per-target validation lives, and one place
the resulting frozenset enters annotation building. A parallel path would be the first
divergent `Meta`-key pipeline in the package.

**A build-time failure, not a runtime one**, matching [Schema audit][glossary-schema-audit]:
a typo'd opt-in must not silently fail open into "no path" (invisible) or silently fail
closed into a crash on the first query (late). The type refuses to build and names the
field.

*Alternatives rejected: see the [rationale][rationale] (a schema-wide settings key, a
consumer-authored `strawberry.field` as THE answer, a marker on the Django model field, a
negative `Meta.hide_filesystem_path` key).*

### Decision 3 — Path failures stay narrow, and are never masked

`_safe_file_attr`'s narrow `(ValueError, OSError, NotImplementedError)` catch is unchanged,
and `SuspiciousFileOperation` continues to propagate. Nothing about the guard widens.

The audit's instruction — "do not mask path failures while continuing to expose successful
absolute paths" — describes a specific incoherence: a guard that swallows the *failure* to
compute a path is only defensible if the *success* is also withheld, otherwise the package
is treating the value as dangerous only when it cannot produce it. This card resolves that
incoherence by **removing the successful path from the default**, not by widening the guard
to swallow more.

Widening the catch would be a strict regression. A broader `except Exception` around a
storage call hides a misconfigured backend, a credential failure, and a real bug behind a
`null`, which is precisely the shape the package refuses elsewhere. And the fields that
*remain* in the default — `size` and `url` — must keep degrading safely on a remote storage
backend that cannot answer, which the existing narrow guard already does and which the test
plan re-pins.

### Decision 4 — The break is justified, and carries a one-line migration

`path` disappears from every generated file and image output in the default schema. This is
a compatibility break for any client selecting it.

It is justified on the same terms cards 046 and 047 used: the API freeze begins at `1.0.0`;
the current default is a confirmed security-boundary defect; the correction is discovered at
schema build or at query time as a clear "field does not exist" rather than as silent
behavior drift; and every shim that preserves the old behavior for one more release
preserves the disclosure for one more release on schemas that never asked for it.

The migration note is one line of `Meta` and one SDL type rename:

```python
class DocumentType(DjangoType):
    class Meta:
        model = Document
        fields = ("id", "title", "attachment")
        filesystem_path_fields = ("attachment",)   # NEW: restores `path`
```

with the consequence that `attachment`'s type name in the SDL becomes
`DjangoFilePathType` (or `DjangoImagePathType`). A client whose query names the type in a
fragment condition or an inline fragment updates that name; a client that only selects
fields does not change at all. The note lands in `docs/README.md` and in `README.md` prose,
where a migrating reader is already looking.

*Alternatives rejected: see the [rationale][rationale] (a warning deprecation release, a
settings flag restoring the old default, narrower path-less siblings beside an unsafe
default).*

### Decision 5 — The debug extension fails CLOSED under `DEBUG=False`, by going inert

[`DjangoDebugExtension`][glossary-djangodebugextension] gains the `__init__` it lacks:

```python
def __init__(self, *, allow_unsafe_production: bool = False) -> None: ...
```

Keyword-only, defaulted to the safe value. Strawberry constructs a bare class entry with
**zero arguments**, so the ubiquitous spelling `extensions=[DjangoDebugExtension]` gets the
safe default for free — the safe path requires no consumer action, which is the property
that makes it a default rather than a suggestion. The documented acknowledgement spelling is
the factory the audit itself names:

```python
extensions=[lambda: DjangoDebugExtension(allow_unsafe_production=True)]
```

**The acknowledgement must be a real `bool`, and a non-bool is a
[`ConfigurationError`][glossary-configurationerror] at construction** — never a truthiness
test. Every string a deployment plausibly reaches for here is TRUTHY: an environment
variable read straight through, `"false"`, `"0"`, `"no"`. Interpreting one would ARM the
production disclosure in the very act of refusing it, which is the worst available failure
mode for the gate that decides whether a response carries unmasked tracebacks and
interpolated SQL. This is `ErrorPolicy.__post_init__`'s rule applied to the same kind of
flag, and it fails at construction — so a schema carrying a misspelled acknowledgement
fails when the engine builds the per-operation instance rather than answering that
operation with the disclosure.

A factory, not a pre-built instance, so the fresh-per-operation contract
([Per-operation extension isolation][glossary-per-operation-extension-isolation]) still
holds. A shared instance is refused / warned by the engine exactly as today; this card adds
no new instance handling and removes none.

At operation start the extension reads `django.conf.settings.DEBUG`. When it is false and
`allow_unsafe_production` is absent, the extension is **INERT**: it acquires no debug
cursor, takes no query-log snapshot, builds no payload, and `get_results()` returns `{}`. It
also logs **one** warning through the package logger, naming the schema misconfiguration, so
the condition is discoverable in a log rather than only as an absent key.

Inertness is chosen carefully, and each half matters:

- **It is fully inert, not merely payload-suppressed.** Building the payload and then
  discarding it would still force `force_debug_cursor` on every connection, which changes
  the database wrapper's behavior and costs memory on the query log for an operation that
  will publish nothing. The gate belongs before the acquisition, not after it.
- **It reads `DEBUG` at operation start, not at import.** `settings.DEBUG` is legitimately
  overridden per test and per settings module, and an import-time read pins whichever value
  happened to be live when the module first loaded.

*Alternatives rejected: see the [rationale][rationale] (raising at operation start — a
denial-of-service lever, refusing at schema construction, a global settings key, gating on
a package-owned production flag instead of `DEBUG`).*

### Decision 6 — Deterministic, marked payload caps as module constants

`extensions/debug.py` grows six module-level constants, and no settings key:

| Constant | Value | Bounds |
|---|---|---|
| `_MAX_SQL_ROWS` | `100` | SQL rows admitted to the payload. |
| `_MAX_EXCEPTION_ROWS` | `25` | Exception rows admitted to the payload. |
| `_MAX_SQL_TEXT_CHARS` | `4096` | Characters of one serialized SQL statement. |
| `_MAX_EXCEPTION_MESSAGE_CHARS` | `4096` | Characters of one exception message. |
| `_MAX_EXCEPTION_STACK_CHARS` | `16384` | Characters of one serialized traceback. |
| `_MAX_PAYLOAD_TEXT_CHARS` | `262144` | Summed characters of the admitted rows' variable-length STRING values. |

**No settings key**, per [`AGENTS.md`][agents]: a bound on a development-only diagnostic that
nobody has asked to tune does not need a public knob, and adding one preemptively is the
mistake `START.md` records. A deployment that needs a different ceiling has a
`DjangoDebugExtension` subclass available.

Truncation is **deterministic and marked**:

- An over-long string is cut to its first N characters and suffixed with the single shared
  literal `_TRUNCATION_MARKER = "... [truncated]"`. One literal, one helper, so a consumer
  can detect truncation with one comparison rather than three.
- **Rows beyond the row cap are dropped from the TAIL.** The earliest queries are the ones
  that explain how the operation started, and a diagnostic that keeps only the last hundred
  of a thousand queries tells you about the symptom rather than the cause.
- **Admission also stops once the running character total would exceed
  `_MAX_PAYLOAD_TEXT_CHARS`**, so a payload cannot be enormous through many rows that each
  fit their own cap. The constant is named for what it measures: the summed length of the
  rows' variable-length string values. It is deliberately **not** a ceiling on the encoded
  payload's byte size — the fixed cost of keys, quoting, separators, and numeric values is
  excluded, because that cost belongs to the wire encoder rather than to the diagnostic, and
  counting it would move the budget whenever the encoder moved. The variable text is the
  part an operation can inflate without bound, and that is the part this bounds.
- **The budget is spent on EXCEPTION rows before SQL rows**, which is a second ordering,
  independent of the row-count cap's keep-the-earliest rule. A failing operation whose
  tracebacks exhaust the budget therefore publishes no SQL at all: the exception rows are
  the ones that explain the failure the reader came for.

**Both lists remain always present**, even when empty and even when every row was dropped.
The wire contract established by spec-044 — `debug.sql` and `debug.exceptions` are lists —
is unchanged, so [Response-extension merge semantics][glossary-response-extension-merge-semantics],
the [Response-extensions debug middleware][glossary-response-extensions-debug-middleware],
and the [Graphene debug migration][glossary-graphene-debug-migration] mapping all keep
working against a capped payload.

**The ordering rule is contractual: caps apply AFTER serialization and BEFORE the payload is
stashed**, in one shared helper that both the SQL and the exception paths call. Truncating
before serialization would mean truncating a structure rather than a string and would give
the two paths different definitions of "too long"; truncating after the stash would mean the
uncapped payload existed in memory, which is the thing being bounded. One helper means the
two paths cannot drift on marker text, cut position, or the running total.

### Decision 7 — `DjangoSchema` gets a first-class production error policy, shaped like the resource policy

Four new surfaces, each mirroring an existing one:

- **`django_strawberry_framework/error_policy.py`** (new) owns a frozen dataclass:

  ```python
  @dataclass(frozen=True)
  class ErrorPolicy:
      enabled: bool = True
      message: str = "An unexpected error occurred."
      correlation_extension_key: str = "correlationId"
  ```

  plus `DEFAULT_ERROR_POLICY` and `resolve_error_policy(explicit)`, which mirrors
  `resource_policy.py::resolve_resource_policy` field for field: explicit instance >
  explicit mapping applied over the defaults > `DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]`
  mapping > package defaults, with an unknown key raising
  [`ConfigurationError`][glossary-configurationerror] naming it.
- **`conf.py::error_policy_setting()`** with `ERROR_POLICY_KEY = "ERROR_POLICY"` — a thin
  reader that validates nothing, exactly like `resource_policy_setting()`. `conf.py` stays a
  reader; the policy object owns every domain check.
- **`extensions/error_policy.py::DjangoErrorPolicyExtension`** performing the masking, plus
  the two module-level seams the transport layer shares: `mask_execution_result` (classify,
  replace, degrade closed) and `schema_error_policy` (read the schema's policy). The policy
  read is **`isinstance`-guarded**, exactly as
  `extensions/resource_policy.py::DjangoResourcePolicyExtension._resolved_policy` guards its
  own: a bare `getattr(schema, "error_policy", DEFAULT_ERROR_POLICY)` answers the default
  only when the attribute is ABSENT, so a schema carrying something that is not an
  `ErrorPolicy` — a mapping, a string, a stray assignment on a consumer subclass — would be
  asked `policy.enabled` and either raise or be read for truthiness, silently disabling
  masking. Any wrong shape falls back to `DEFAULT_ERROR_POLICY`, which is the masking
  answer.
- **`schema.py::DjangoSchema.__init__`** grows
  `error_policy: ErrorPolicy | Mapping[str, Any] | None = None`, resolves it once at
  construction, exposes `schema.error_policy`, and installs the extension.

**Resolved once at construction** so an invalid deployment fails at startup rather than on
the first request that happens to raise. **Frozen** so a resolver holding the policy cannot
loosen it. **Mirroring the resource policy exactly** so the package has one policy-object
idiom rather than two similar ones — a future third policy has an obvious shape, and a
reader who has understood one has understood all of them.

Opt-out is explicit and has two spellings, both deliberate:
`DjangoSchema(error_policy={"enabled": False})` disables the masking while keeping the
extension installed (so the shape is auditable), and supplying a
`DjangoErrorPolicyExtension` entry of your own suppresses the automatic install entirely —
exactly as a consumer-supplied
[`DjangoResourcePolicyExtension`][glossary-djangoresourcepolicyextension] suppresses
`_with_resource_policy_extension`'s append. Consumer code remains trusted; it simply has to
say so.

*Alternatives rejected: see the [rationale][rationale] (a boolean `mask_errors=True`, a
settings-key-only configuration, validating in the settings reader instead of the
dataclass).*

### Decision 8 — The classification rule is STRUCTURAL, not an allowlist

In the extension's `on_operation` teardown, each error on the result is classified by
**shape**, not by code:

| Condition | Verdict |
|---|---|
| `error.original_error is None` | A parse or validation error. **Untouched.** |
| `isinstance(error.original_error, GraphQLError)` | A deliberate client-facing error. **Untouched.** |
| anything else | Unexpected. **Masked.** |

**The rule reads through graphql-core's `located_error` wrapping, which is what makes it
cover the COMPLETION phase and not merely the resolve phase.** Every exception graphql-core
surfaces from a field arrives as a `GraphQLError` whose `original_error` is that exception —
whether it escaped the resolver, escaped an awaited value, or was raised while *completing*
the resolved value: non-nullable `null` propagation, list-item completion, a custom scalar's
`serialize`. So a resolver failure that reaches the client through completion is still an
unexpected plain exception here and is still masked, and graphql-core's own completion
`TypeError` is masked for the same structural reason — the fail-closed direction, and a
message a client can always re-derive from the schema it already has. A masked surface with
a hole shaped like the completion phase would look identical to a correct one on every
resolve-phase test, so the two completion shapes carry live rows of their own.

Because of that wrapping, the `original_error is None` row is NOT reached by anything
graphql-core builds during execution. Its real traffic is the parse/validation path, and on
the ASYNC transports that path reaches the teardown as a strawberry `PreExecutionError`
(which IS an `ExecutionResult`, so the shape gate admits it) carrying errors with nothing
behind them.

The second row is the whole decision. **Every framework rejection in this package is raised
as a `GraphQLError`** — the GlobalID rejections (`GLOBALID_INVALID`), `ResourceLimitExceeded`
(`RESOURCE_LIMIT_EXCEEDED`, which multiple-inherits `GraphQLError` on the
[`SyncMisuseError`][glossary-syncmisuseerror] precedent), the connection / keyset / filter
rejections, and `mutations/resolvers.py`'s `"Not authorized to ..."` permission denial. A
consumer who raises a `GraphQLError` from their own resolver is making the identical
statement: *this message is for the client*. So the rule is not a heuristic about this
package's internals; it is the GraphQL type system's own way of saying "client-facing".

The rule is structural rather than a curated `extensions.code` allowlist because the two
fail in opposite directions: an unmaintained allowlist masks the next deliberate rejection
(fails open), while the structural rule masks every unregistered plain exception by
default. **It fails CLOSED for exactly the class of thing that is dangerous, and fails open
only for something a developer explicitly typed as client-facing.** *The full comparison is
in the [rationale][rationale].*

[`FieldError` envelopes][glossary-fielderror-envelope] need no rule at all: a validation
failure from a form or serializer mutation is returned in `data` as a structured payload,
not raised as an error. They are untouched **by construction**, and this is stated so a
future reader does not add a redundant carve-out for them.

*Alternatives rejected: see the [rationale][rationale] (a curated `extensions.code`
allowlist, a module-prefix check on the spoofable `__module__`, an opt-in exception base
class).*

### Decision 9 — Masking is gated on `DEBUG`, and the correlation id is what reaches the client

**When `settings.DEBUG` is true the policy is a pass-through.** Development keeps its real
messages; a masked stack trace in a developer's browser is a worse day for everyone and
teaches the developer to disable the policy wholesale. Read at operation time, for the same
reason Decision 5 reads it there.

When `DEBUG` is false and `policy.enabled` is true, each unexpected error is **replaced**,
not mutated, by a fresh error:

```python
GraphQLError(
    policy.message,
    nodes=error.nodes,
    source=error.source,
    positions=error.positions,
    path=error.path,
    original_error=None,
    extensions={policy.correlation_extension_key: correlation_id},
)
```

- **The original `nodes` / `source` / `positions` / `path` are retained.** A client still
  learns WHICH field failed, which is not sensitive — the schema is public and the client
  wrote the query. Dropping them turns every partial failure into an unattributable one and
  breaks client-side error-to-field mapping for no security gain.
- **`original_error=None`** so nothing downstream (another extension, a logger, a
  transport) can recover the message from the object that reaches the wire.
- **A fresh object, not an in-place edit**, because a `GraphQLError` mutated in place may
  still be referenced by whatever raised it, and because "replace the entry in
  `result.errors`" is a single, auditable operation.

**The id format is pinned: `uuid.uuid4().hex`** — 32 lowercase hex characters, no dashes,
grep-safe, log-safe, URL-safe, and safe to read aloud over a support call. Random rather
than derived: a hash of the message or the traceback would be an oracle, letting a client
distinguish two errors or confirm a guess about the exception text.

**One fresh id PER MASKED ERROR, not per operation.** A response carrying two unrelated
failures logs two exceptions; a single per-operation id would make the client's report
ambiguous about which of them they hit, which is the exact question the id exists to answer.

**The log destination is pinned**: the package logger `django_strawberry_framework` (the
`logger` in `django_strawberry_framework/__init__.py`), at `ERROR`, with `exc_info` set to
the original exception, and **the correlation id in the message text** so a deployment with
plain-text logging and no structured `extra` handling still resolves a client's report with
one `grep`.

**Message configurability is pinned**: `ErrorPolicy.message`, settable through the schema
argument or the setting. A single stable string with **no interpolation** of the original
error, the exception type, or the field name — an interpolated message is a disclosure
channel wearing a template's clothes, and the whole card is about not having one.

*Alternatives rejected: see the [rationale][rationale] (Strawberry's `MaskErrors`,
overriding `Schema.process_errors`, a per-operation single id, omitting
`path` / `locations`, a counter or derived hash as the id).*

### Decision 10 — Extension ORDER is load-bearing, and the install PREPENDS

`DjangoErrorPolicyExtension` is inserted at **index 0** of the extensions list, not appended.

`on_operation` teardowns unwind **LIFO**, so the FIRST-listed extension tears down **LAST**.
Prepending therefore guarantees the policy masks *after* everything else has had its turn —
critically, after [`DjangoDebugExtension`][glossary-djangodebugextension], which must read
`original_error` to build its exception rows and whose docstring already documents
"list after any masking extension"
([Masking-extension ordering][glossary-masking-extension-ordering]). It also runs after any
consumer masking extension, so a consumer's own policy sees the originals it expects.

**This is the exact inverse of `_with_resource_policy_extension`'s append, and the inversion
is principled rather than incidental.** The resource policy does its work in the **setup**
half — it gates a request before execution, and setup runs in list order, so appending
places it after every consumer extension has established whatever context it needs. The
error policy does its work entirely in the **teardown** half, and teardown runs in reverse
list order, so prepending places it after every other extension's teardown. **One rule
states both: put the extension where its own half of the lifecycle runs LAST**, because
both policies are the final word on their side of the operation. Slice 3 pins this with a test asserting the resolved extension order
on a `DjangoSchema` that also carries the debug extension, so a future refactor that
"tidies" the install into a symmetric append fails loudly rather than silently un-masking
the debug payload's exception rows.

*Alternatives rejected: see the [rationale][rationale] (appending for symmetry, documenting
the order for the consumer, masking in `get_results` or in the view).*

### Decision 11 — Sync/async parity comes from the hook; a STREAMED operation needs a second seam

The teardown is **one synchronous generator** serving both execution colors — the engine
enters sync generator hooks on the async path too. This is the precedent
[`DjangoDebugExtension`][glossary-djangodebugextension] already set with its own
`on_operation`, and it is why there is exactly one masking implementation and no
color-specific branch to keep in step.

The single implementation handles both result shapes it can be handed: graphql-core's
`ExecutionResult` and Strawberry's `ExecutionResult` — the shared shape gate is
`is_maskable_result`, which both seams ask so neither can drift on the question. Both
admitted shapes expose an `errors` sequence; the masking reads it, replaces the entries it
must, and the extension assigns the list back. A result that is `None` (a sync
parse/validation early return), carries no errors, or is not an admitted shape is a no-op.

**One seam is not enough, because a response is not always one result.** A query or a
mutation answered through `schema.execute` produces exactly one already-torn-down
`ExecutionResult`, so the operation teardown IS the response for it. A **streamed
operation** is not: a subscription delivers one `ExecutionResult` per EVENT through the
result source the transport iterates, and a query or mutation run over a streaming
transport (`graphql-transport-ws` dispatches EVERY operation type through `schema.stream`
from strawberry-graphql 0.319.0 on) has its single result yielded from *inside* the
operation lifecycle. Either way the operation teardown runs only when the operation
*ends* — so masking bolted to the teardown alone is a **complete no-op for every streamed
result**: the raw exception message is serialized and sent long before the teardown runs,
and the teardown then rewrites a result nobody reads. Transport parity is therefore NOT a
free structural property; it is a property of applying the policy at every seam that
delivers a result.

The second seam is the package's own streamed-result source,
`consumers.py::_stop_aware_results` — the one generator every result of every streamed
operation passes through on both WebSocket protocols, already owned by this package for the
operation-stop protocol. The stop-aware schema wrapper defines **both** upstream dispatch
names, `subscribe` and `stream`, unconditionally and routes them through one shared
wrapping step, so the two cannot diverge on what a result source is wrapped with; `execute`
stays delegated because it returns one already-torn-down result and never loops. The seam
masks each yielded result immediately before the transport renders it, through the same
`mask_execution_result` the teardown uses: one classifier, one replacement builder, one
degrade policy, two application sites. `stream`'s third element type — a raw graphql-core
incremental-delivery frame (`@defer` / `@stream`), whose errors are nested inside
incremental payloads rather than on an `errors` attribute — is excluded by
`is_maskable_result` and passes through untouched: masking it would produce the fail-closed
degrade, whose value IS an `ExecutionResult`, precisely the shape upstream's transport
tests for to decide a frame is unrenderable and the operation must be rejected. Excluding
it by shape leaves that rejection intact and discloses nothing — the frame never reaches
the wire at all. Two further properties are pinned:

- **Masking returns a masked COPY, never an in-place rewrite.** The object the engine
  assigned to `execution_context.result` keeps its originals, so
  [`DjangoDebugExtension`][glossary-djangodebugextension] — and any consumer extension that
  reads `GraphQLError.original_error` — still reads what was raised. That is what keeps
  [Decision 10](#decision-10--extension-order-is-load-bearing-and-the-install-prepends)'s
  LIFO ordering promise true on the subscription path as well as the query path.
- **The policy object is resolved once per subscription; the `DEBUG` pass-through is read
  per event**, which is the same granularity the teardown reads it at.

A pre-execution error on a subscription (`PreExecutionError`, the operation-scoped `error`
frame) travels through the same seam and passes the classifier untouched, because a
validation error carries no `original_error`.

*Alternatives rejected: see the [rationale][rationale] (the transport's frame writer, a
schema subclass, accepting the gap for subscriptions, an upper strawberry version bound
instead of wrapping the renamed upstream seam). The two rewrites this decision underwent —
the remediation round's seam addition and the post-release `stream` coverage, including the
audited `{subscribe, stream, execute}` upstream read set across `0.316.0`-`0.323.2` — are
in the change record there.*

### Decision 12 — The version bump belongs to the `0.0.14` joint cut

This card does **not** move the version quintet. It targets `0.0.14`, sharing that patch
with cards 041-045 and with its three program siblings (046, 047, 049). The quintet —
`pyproject.toml [project].version`, `django_strawberry_framework/__init__.py::__version__`,
the `tests/base/test_init.py` assertion that pins them together, the glossary's
package-version line, and the package's own `uv.lock` entry — already reads `0.0.14`, so
there is no bump for this card to take.

Under the [joint version cut][glossary-joint-version-cut] rule the release wording belongs
to the **last** card of a shared line to land, never to an individual card's slices.
Slice 5 therefore owns the documentation fold-in only.

*This card was authored and built against a `0.0.17` cut of its own. What it claimed, and
the program-wide retarget that withdrew it, is in the [rationale][rationale].*

### Decision 13 — What the masking rule does not reach, and the two seams it still owes

**Decision.** The consequences below follow from
[Decision 8](#decision-8--the-classification-rule-is-structural-not-an-allowlist)'s structural
rule and from where the masking hook is installed. Two are **owed work**; two are **deliberate
boundaries** a later pass must not read as gaps.

**Owed — upstream's own argument rejections are masked.** The rule is structural rather than an
allowlist, so an error is left untouched when it carries a code the package audits. Strawberry's
relay and pagination **argument** rejections carry none, so they fall into the masked branch and
reach the client as `policy.message` plus a correlation id — a client that passed a bad `first` /
`last` combination learns nothing actionable. The fix is **not** to loosen the rule: it is for the
package to raise those rejections as a `GraphQLError` carrying an audited `extensions.code`, which
brings them under the untouched branch the rule already has. That is a behaviour change this
spec does not license, so it is stated here rather than done.

**Owed — the subscription masking rows are consumer-tier, not live.** `examples/fakeshop` has no
subscription app and the live tier cannot reach a WebSocket through `django.test.Client`, so the
per-event masking rows live in `tests/test_routers.py`. Under the
[live-first coverage mandate][glossary-live-first-coverage-mandate] that is a substitution, not a
preference, and a fakeshop subscription surface is its own card.

**Boundary — a consumer-built plain `GraphQLWSConsumer` gets no per-event masking.** The seam is
installed by `consumers.py::build_revalidating_consumer_class`, which the package router builds.
A consumer who constructs `strawberry.channels.GraphQLWSConsumer` directly therefore keeps
upstream's unmasked per-event delivery. This is the **same** boundary the operation-stop protocol
already has, and it is the documented reason the package router is the supported mount rather than
one option among several.

**Boundary — non-WebSocket subscription transports have no seam here.** The package's own
subscription seam is the Channels consumer result source, and nothing in the package serves
subscriptions over HTTP today. If a future card exposes subscriptions over multipart or SSE
through a package-owned view, that transport needs the same `mask_execution_result` call at its
own per-event delivery point; the requirement travels with the transport that creates it.

**Deliberate — the debug payload caps are not configurable, and that is not an omission.**
[`AGENTS.md`][agents] pins the rule: add a settings key when the feature that needs it lands, not
in anticipation. A deployment wanting a different ceiling is a deployment running the debug
extension in production, which
[Decision 5](#decision-5--the-debug-extension-fails-closed-under-debugfalse-by-going-inert)
already refuses by default. Revisit only if a real consumer need appears — not because six module
constants look like they want a setting.

## Implementation plan

| Slice | Files | Delta |
|---|---|---|
| 1 | `types/converters.py` | `path` moves to `_FileSystemPathFields`; `DjangoFilePathType` / `DjangoImagePathType`; the safe-to-path type mapping; `convert_field_output(..., expose_filesystem_path=…)`. |
| 1 | `types/base.py` | `filesystem_path_fields` in the `_ValidatedMeta` snapshot and the `Meta`-key allowlist; the four-failure validation pass; the frozenset threaded into `_build_annotations`. |
| 1 | `__init__.py`, `types/__init__.py` | Exports for the two new public output types. |
| 2 | `extensions/debug.py` | `__init__(*, allow_unsafe_production=False)`; the operation-start `settings.DEBUG` gate and its single warning; the six caps, `_TRUNCATION_MARKER`, and the one shared truncation/admission helper called by `_serialize_sql_row` and `_serialize_exception` before `_build_payload` stashes. |
| 3 | `error_policy.py` (new) | `ErrorPolicy`, `DEFAULT_ERROR_POLICY`, `resolve_error_policy`. |
| 3 | `conf.py` | `ERROR_POLICY_KEY` and `error_policy_setting()`, a thin reader that validates nothing. |
| 3 | `extensions/error_policy.py` (new) | `DjangoErrorPolicyExtension`: the teardown, the structural classifier, the replacement builder, the correlation id, the log call, the two fail-closed degrades, and the `isinstance`-guarded `schema_error_policy` read. |
| 3 | `consumers.py` | `_stop_aware_results` masks each streamed result through `mask_execution_result` (under the shared `is_maskable_result` gate) before the transport renders it; the stop-aware schema wrapper defines `subscribe` AND `stream` through one shared wrapping step and hands the real schema through so the policy is the executing schema's (Decision 11). |
| 3 | `extensions/__init__.py`, `__init__.py` | Exports; the extension is root-exported because it is part of the default recipe. |
| 3 | `schema.py` | `DjangoSchema(error_policy=…)`, `schema.error_policy`, `_with_error_policy_extension` (prepending). |
| 4 | `examples/fakeshop/test_query/`, `examples/fakeshop/apps/*/tests/`, `tests/` | The rows in [Test plan](#test-plan). |
| 5 | `docs/GLOSSARY.md` (DB), `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, `KANBAN.md` (DB) | Fold-in and the migration note. |

## Helper-reuse obligations (DRY)

- **`_FileSystemPathFields` is the only `path` resolver.** No second definition, in the
  package or in the example project.
- **`_safe_file_attr` remains the only storage-attribute guard**, and the new mixin uses it
  unchanged. A new file attribute does not get its own `try`.
- **The `_ValidatedMeta` normalization helper is the only `Meta`-sequence normalizer.**
  `filesystem_path_fields` uses the same `_normalize_sequence_spec` the override sets use.
- **One truncation helper** in `extensions/debug.py` owns the marker, the cut, and the
  running payload total. Neither serializer may open-code a `[:N]`.
- **`resolve_error_policy` mirrors `resolve_resource_policy`'s ladder**; neither grows a
  second precedence rule, and a future third policy copies the same shape.
- **`ErrorPolicy.__post_init__` is the only validation gate** for the error policy;
  `conf.py` validates nothing.
- **`DjangoErrorPolicyExtension`'s classifier is one function**, and the replacement builder
  is one function, so the sync and async result shapes cannot diverge on either.
- **`mask_execution_result` is the ONLY application of the policy**, called by the operation
  teardown and by `consumers.py::_stop_aware_results`. The transport seam re-states no
  classification, no replacement shape, no correlation id, no `DEBUG` gate, and no shape
  gate — it calls `masking_is_active` for the gate, `schema_error_policy` for the policy,
  and `is_maskable_result` for the shape, like the extension does.
- **[`request_from_info`][glossary-request_from_info] is the only info-to-request seam** if
  the extension ever needs the request; it does not re-derive one.

## Edge cases and constraints

- **A `FileField` on a model but not selected by [`Meta.fields`][glossary-metafields]** and
  named in `filesystem_path_fields` is a `ConfigurationError`, not a silent no-op — a
  declaration that does nothing is a bug the consumer wants to hear about.
- **An `ImageField` opted in** yields `DjangoImagePathType`, never `DjangoFilePathType`; the
  mapping is keyed on the resolved safe type, which the existing MRO walk already produced,
  so a consumer `ImageField` subclass follows automatically.
- **An empty `filesystem_path_fields = ()`** is legal and means exactly the default. It is
  not an error, so a configuration generator can emit the key unconditionally.
- **A remote storage backend that raises `NotImplementedError` for `path`** still degrades
  to `null` on an opted-in field, through the unchanged `_safe_file_attr`; `size` and `url`
  keep degrading on the retained fields.
- **`SuspiciousFileOperation` still propagates** from every file attribute, opted-in or not.
- **The example project's aggregate schema keeps `path` off every DEFAULT output**, which a
  live introspection probe over `/graphql/` proves: `DjangoFileType` / `DjangoImageType`
  publish no `path` field, and `MediaSpecimenType` keeps both of its columns on them. The
  opt-in is demonstrated in the SAME live schema rather than in a throwaway probe schema, by
  a second type over the same model — `MediaSpecimenWithPathType`, `primary = False`, naming
  `attachment` and deliberately NOT `image`. That is the stronger arrangement and it is what
  ships: the per-column claim is only worth anything against a schema where an un-opted
  column exists beside an opted-in one, and the live rows pin exactly that (`attachment` is
  `DjangoFilePathType` and resolves a real absolute path, `image` stays `DjangoImageType`,
  and the same request cannot even ask `MediaSpecimenType` for a path).
- **The debug extension under `DEBUG=False` with the acknowledgement** behaves exactly as
  today, caps included. The acknowledgement suppresses the gate, not the caps.
- **The debug warning fires once per operation**, on the operation that was gated — not once
  per process. A per-process warning is invisible in a long-lived worker that started before
  the misconfiguration mattered.
- **An operation that produces no SQL and no exceptions** still publishes both lists, empty,
  under `DEBUG=True`. Caps never remove a key.
- **No single row can be refused by the payload budget on its own.** The per-row limits
  bound one row's text to at most ~20K characters, an order of magnitude below
  `_MAX_PAYLOAD_TEXT_CHARS`, so "the first row already exceeds the budget" is unreachable by
  construction rather than a case with a fallback. Admission stops at the first row that
  would exceed the RUNNING total, which only a row with predecessors can do.
- **An error with `original_error` set to a `GraphQLError` that itself wraps a plain
  exception** is untouched: someone deliberately wrapped it and chose the outer message.
- **An error raised during masking itself** must not replace the response with an internal
  failure, and must not fall back to the text it was masking either — leaving the entry as
  it was found publishes exactly what the policy exists to withhold, on the one path nobody
  exercised. So masking degrades CLOSED, at two levels: one error that cannot be classified
  or replaced becomes the policy message alone (no location, no correlation id — nothing is
  read off the error whose read just failed), and a result whose error list cannot be read at
  all becomes a single policy-message error with no `data`. Both degrades log server-side
  with a traceback, so the failure is diagnosable without being publishable. The per-entry
  degrade is what keeps the common case faithful in order and arity; the outer one is the
  floor.
- **`policy.enabled = False`** leaves the extension installed and the teardown a no-op, so
  the opt-out is visible in the schema's extension list.
- **A schema constructed with `DEBUG=True` and executed with `DEBUG=False`** masks, because
  the gate is read at operation time; a settings override in a test therefore takes effect
  without rebuilding the schema.
- **A correlation id is generated only for errors that are actually masked**, so an
  operation whose only failure was a deliberate rejection writes no error log line.
- **A streamed operation's errors are masked PER YIELDED RESULT**, at
  `consumers.py::_stop_aware_results` — every subscription event on both WebSocket
  protocols, and the single result of a query or mutation dispatched through
  `schema.stream` — each masked error with its own correlation id and its own log record.
  The operation teardown still runs at the operation's end, and by then it has nothing left
  to do — every result was masked on its way out (Decision 11).

## Test plan

Placement follows [`AGENTS.md`][agents] rules 7 and 10 and the
[live-first coverage mandate][glossary-live-first-coverage-mandate]: anything reachable
through a real GraphQL query goes to `examples/fakeshop/test_query/` over HTTP via
[`TestClient`][glossary-testclient]; a [probe URLconf][glossary-probe-urlconf] mounts the
package view over a narrow probe schema when the aggregate fakeshop schema cannot express
the case; `tests/` covers only what no request can reach. Every catalog row opens with
[`seed_data(N)`][glossary-seed_data].

**Live tier — `examples/fakeshop/test_query/test_uploads_api.py`.** The file/image output
surface already has a live home, so the rows land there rather than in a new file:

- The aggregate fakeshop SDL contains **no** `path` field and no `DjangoFilePathType` /
  `DjangoImagePathType`; a query selecting `path` on a file field is a validation error
  naming the unknown field.
- The retained fields still answer: `name`, `size`, `url` on a real file-bearing row, and
  the same three degrading to `null` (not erroring) when the storage backend cannot report,
  proving Decision 3's narrow guard is intact.
- The SHIPPED aggregate schema's own `MediaSpecimenWithPathType` (`primary = False`, naming
  `attachment` only) exposes `DjangoFilePathType` with a working absolute `path`, while its
  own `image` stays `DjangoImageType` — the per-column claim, made against a schema where an
  un-opted column sits beside the opted-in one.
- The opt-in is absent unless declared: `MediaSpecimenType`, over the same model without the
  key, has no `path` at all, and the same request that reads a path off the opted-in type
  cannot even ask the default type for one.

**Live tier — `examples/fakeshop/test_query/test_debug_extension_api.py`.**

- Under `DEBUG=False`, a probe schema listing `DjangoDebugExtension` returns **no** `debug`
  key, and one warning is captured on the `django_strawberry_framework` logger.
- Under `DEBUG=False` with `lambda: DjangoDebugExtension(allow_unsafe_production=True)`, the
  payload is present and complete.
- Under `DEBUG=True`, the bare class publishes as today (the regression guard for the gate).
- The aggregate fakeshop schema publishes no `debug` key at all under either `DEBUG` value —
  the "stays debug-free" row.
- Payload caps truncate deterministically over a probe query driving many queries and a long
  statement: the row count stops at `_MAX_SQL_ROWS`, the retained rows are the **earliest**,
  each over-long string ends with `_TRUNCATION_MARKER`, and both lists are present.
- Fresh-instance isolation: two sequential operations on the same schema publish
  independent payloads, with the second not carrying the first's rows.

**Live tier — `examples/fakeshop/test_query/test_error_policy_api.py`.**

- Under `DEBUG=False`, a probe resolver raising `ValueError("internal tenant secret
  /srv/private")` returns the policy message, a 32-hex-character correlation id under
  `correlationId`, the original `path`, and **not** the original text anywhere in the
  response body.
- The matching log record exists on the `django_strawberry_framework` logger at `ERROR`,
  carries the same id in its message, and has `exc_info` set.
- Untouched classes, one row each: a parse error, a validation error, a
  `GLOBALID_INVALID` rejection, a `RESOURCE_LIMIT_EXCEEDED` rejection, a
  `"Not authorized to ..."` permission denial, and a
  [`FieldError` envelope][glossary-fielderror-envelope] returned in `data`.
- A consumer resolver raising its own `GraphQLError` is untouched.
- Two unexpected failures in one response carry **two different** ids and produce two log
  records.
- Under `DEBUG=True`, the literal message is returned (the pass-through row).
- `DjangoSchema(error_policy={"enabled": False})` returns the literal message under
  `DEBUG=False`.
- A custom `message` and a custom `correlation_extension_key` both reach the wire.
- Sync/async parity: the sync and async mounts return byte-identical error entries apart
  from the id itself.
- Ordering: a schema carrying both `DjangoDebugExtension` and the auto-installed policy
  publishes a debug payload whose exception rows carry the **original** exception type and
  message while the client-facing error is masked — the direct proof of Decision 10.

**Consumer tier — `tests/test_routers.py`.** The subscription seam, which only the transport
can observe (Decision 11): a subscription emitting TWO events whose payload field raises
delivers two masked frames on BOTH protocols — the policy message, a distinct 32-hex
correlation id per event, the retained `path`, the successful part of `data` intact, the
exception's own text absent from the raw frame, and one server-side log record per id
carrying the original exception. Requiring two events is what separates per-delivery masking
from a single pass over a final result. The control row on the same subscription with
`error_policy={"enabled": False}` returns the resolver's own message, so the seam is the
policy's and not a blanket rewrite. A transparency row re-derives, from the installed
upstream handler modules, the set of names they read off the schema they were handed and
proves it a partition — every read is a wrapper-defined name (`subscribe`, `stream`),
derived from the class rather than restated, or an explicitly reasoned delegation
(`execute`) — so an unaudited NEW upstream dispatch name fails loudly instead of silently
bypassing the seam.

**Package tier — `tests/test_error_policy.py`.** What no request can express: every
`ErrorPolicy` field's validation including the unknown-key rejection; the three-level
precedence ladder; the settings-shape rejections; `resolve_error_policy` idempotence on an
instance; the classifier over each of the three structural cases directly; the replacement
builder's field-for-field preservation and its `original_error=None`; the `None`-result and
empty-errors no-ops; both `ExecutionResult` shapes; the `isinstance`-guarded policy read over
every wrong attribute shape; both fail-closed degrades (an error object whose
`original_error` raises, a result whose `errors` cannot be read); and
`mask_execution_result`'s copy contract — same object when nothing was masked, a copy that
leaves the original holding its originals otherwise. The `original_error is None` row runs a
real ASYNC operation that fails validation, because that is the path which actually reaches
the branch.

**Package tier — `tests/types/test_base.py` / `tests/types/test_converters.py` additions.** The
`filesystem_path_fields` `ConfigurationError` rows (unknown, non-selected, consumer-authored,
non-file), the empty-tuple legality row, the normalization of `list` / `tuple` / `set` /
`frozenset` for the opt-in key AND for its sibling keys, the guard's rejection message naming
the key the consumer wrote, and the safe-to-path type mapping over an `ImageField` subclass.

**Package tier — `tests/extensions/test_debug.py` additions.** The `__init__` signature's
keyword-only default, its refusal of every non-bool acknowledgement (`"false"` above all, the
truthy literal that would otherwise arm the disclosure) and the consequence that a schema
carrying one fails when the engine builds the per-operation instance, the gate's
operation-time read, and the truncation helper's exact cut position and marker over a
synthetic string — the pure-function rows a live query cannot pin precisely.

**Base tier.** `tests/base/test_init.py` gains the `ErrorPolicy` /
`DjangoErrorPolicyExtension` / `DjangoFilePathType` / `DjangoImagePathType` export rows and
its version pin stays at `0.0.14`. `tests/base/test_conf.py` gains the
`error_policy_setting()` rows.

## Doc updates

- `docs/GLOSSARY.md` (DB-backed, rendered by `scripts/build_glossary_md.py` — edit the
  fakeshop glossary app's DB and re-render, never hand-edit): new entries for
  **`Meta.filesystem_path_fields`**, **`DjangoFilePathType`**, **`DjangoImagePathType`**,
  **`ErrorPolicy`**, and **`DjangoErrorPolicyExtension`**; a fail-closed-gate paragraph and
  the payload caps folded into [`DjangoDebugExtension`][glossary-djangodebugextension],
  [Developer-only debug posture][glossary-developer-only-debug-posture],
  [Debug SQL row][glossary-debug-sql-row], and
  [Debug exception row][glossary-debug-exception-row]; updated bodies for
  [`DjangoFileType`][glossary-djangofiletype] and
  [`DjangoImageType`][glossary-djangoimagetype] recording the removal, the divergence from
  `strawberry-graphql-django`, and the documented sensitivity of `name`; a note in
  [Masking-extension ordering][glossary-masking-extension-ordering] that the package's own
  policy now prepends.
- `docs/README.md`: the migration note for the `path` removal, and the production-error-
  policy section under the security guidance.
- `docs/TREE.md`: regenerated (`scripts/build_tree_md.py`) for `error_policy.py` and
  `extensions/error_policy.py`; both need module docstrings or the render fails.
- `README.md`: the migration note in prose, and the secure-defaults line in the positioning
  section.
- `TODAY.md`: move the three audit items out of "what products is still waiting for" and
  into the shipped snapshot.
- `KANBAN.md` (DB-backed): card 048 to Done.
- `CHANGELOG.md`: **not** touched. [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits
  without explicit permission, and this card's Slice 5 does **not** claim that permission —
  the release entry is the maintainer's.

## Risks and open questions

Each risk's pre-planned fallback position, should a real consumer need appear, is in the
[rationale][rationale].

- **The `path` removal has no telemetry.** A consumer discovers it as a validation error on
  their next query rather than through a deprecation warning. Accepted, and it is the same
  trade card 047 accepted for the relation-shape default: an immediate, unambiguous failure
  beats a warning nobody reads.
- **The opt-in changes the SDL type NAME, not just the field set.** A client using a
  fragment type condition on `DjangoFileType` against an opted-in field must update it.
  Accepted for `0.0.14`, because the alternative — one type whose fields vary — is not
  expressible in GraphQL.
- **The debug caps are not configurable.** Module constants, per [`AGENTS.md`][agents]'s
  "add a settings key only when the feature needs it".
- **Masked errors log one record each, so an error storm is a log storm.** Accepted — a
  deployment's logging stack already owns rate limiting, and dropping error records to save
  volume would defeat the correlation id.
- **`correlationId` could collide** with a consumer's own extension key. It is configurable
  (`correlation_extension_key`), and the default matches the common convention.
- **The structural classifier trusts consumer `GraphQLError`s.** A consumer who raises
  `GraphQLError(str(exc))` from a bare `except` re-opens the disclosure in their own code.
  Documented — consumer code is trusted, which is the package's standing posture and the
  audit's own framing.
- **`settings.DEBUG` is the gate for two unrelated behaviors** (the debug extension and the
  masking policy), so a deployment that runs `DEBUG=True` in a staging environment reachable
  by untrusted clients gets neither protection. Accepted: that deployment is already outside
  Django's own security model, and inventing a package-specific production flag would create
  a second source of truth that can disagree with Django's.

## Non-goals

Restated for the checklist reader; the reasoning is in
[Non-goals](#non-goals) above — no PII framework, no structured logging, no error-reporting
vendor seam, no `name` removal, no error-path rate limiting, and no time-based debug caps.

## Out of scope (explicitly tracked elsewhere)

- Dependency and CI hardening (S6, S7) — [`WIP-ALPHA-049-0.0.14`][kanban].
- The execution resource policy (S3, S4) — shipped in [`spec-047`][spec-047].
- Transport security (S1, S2, S9, S11) — shipped in [`spec-046`][spec-046].
- Field-level cost annotation — deferred by [`spec-047`][spec-047]'s risks section.
- A declarative sensitive-field / redaction vocabulary — not carded.
- Response-byte accounting — deferred by [`spec-047`][spec-047]; the debug caps here bound
  one diagnostic payload, not the response.

## Definition of done

- [ ] `path` is absent from [`DjangoFileType`][glossary-djangofiletype] and
      [`DjangoImageType`][glossary-djangoimagetype] and from the default generated SDL;
      `DjangoFilePathType` / `DjangoImagePathType` compose one shared, security-described
      `path` resolver and are reachable only through `Meta.filesystem_path_fields`.
- [ ] `Meta.filesystem_path_fields` is validated in the `_ValidatedMeta` snapshot on the
      same terms as [`Meta.nullable_overrides`][glossary-metanullable_overrides] /
      [`Meta.required_overrides`][glossary-metarequired_overrides], raising
      [`ConfigurationError`][glossary-configurationerror] naming the offending field for an
      unknown, non-selected, consumer-authored, or non-file target (a relation being refused
      as a non-file column).
- [ ] `_safe_file_attr`'s narrow catch is unchanged and `SuspiciousFileOperation` still
      propagates; the retained fields still degrade safely on a storage backend that cannot
      answer.
- [ ] [`DjangoDebugExtension`][glossary-djangodebugextension] has a keyword-only
      `allow_unsafe_production` defaulting to `False`, is fully inert under `DEBUG=False`
      without it (no cursor, no snapshot, no payload, `{}` from `get_results`, one warning),
      and behaves exactly as before with it.
- [ ] The debug payload is bounded by six module constants through one shared helper applied
      after serialization and before the stash; truncation is marked with one shared literal,
      rows drop from the tail, and both lists are always present.
- [ ] `ErrorPolicy`, `resolve_error_policy`, `conf.py::error_policy_setting()`, and
      `DjangoErrorPolicyExtension` exist; `DjangoSchema` resolves the policy once at
      construction, exposes `schema.error_policy`, and PREPENDS the extension.
- [ ] Under `DEBUG=False` with the policy enabled, an unexpected exception reaches the
      client as `policy.message` plus a `uuid4().hex` correlation id with its
      nodes / source / positions / path retained and `original_error` cleared, and reaches
      the `django_strawberry_framework` logger at `ERROR` with `exc_info` and the same id in
      the message text; parse errors, validation errors, every framework `GraphQLError`
      code, permission denials, and [`FieldError` envelopes][glossary-fielderror-envelope]
      are untouched.
- [ ] Sync and async transports return identical masked entries from one synchronous hook.
- [ ] Full suite green at `fail_under = 100` for `django_strawberry_framework`; `ruff
      format --check`, `ruff check`, `scripts/check_trailing_commas.py --check`,
      `manage.py check` and `makemigrations --check --dry-run` all clean.
- [ ] Docs folded in with the migration note; the version quintet rides the joint `0.0.14`
      cut ([Decision 12](#decision-12--the-version-bump-belongs-to-the-0014-joint-cut)).

**Carried forward — owed rather than shipped**, and separated from the list above because that
list describes the released contract while these describe work the release left open
([Decision 13](#decision-13--what-the-masking-rule-does-not-reach-and-the-two-seams-it-still-owes)):

- [ ] Upstream's own relay / pagination **argument** rejections reach the client as a
      `GraphQLError` carrying an audited `extensions.code`, so the structural rule's untouched
      branch covers them instead of masking them. Not licensed by this spec, and the fix must
      not loosen the rule to achieve it.
- [ ] `docs/GLOSSARY.md` has a `DjangoSchema` entry, so the constructor's two policy arguments
      are described from the schema side rather than only from the `ErrorPolicy` /
      `ResourcePolicy` side — and [`spec-047`][spec-047]'s glossary rows stop pointing at a
      `#djangoschema` anchor that resolves to nothing.
- [ ] A consumer who builds a plain `strawberry.channels.GraphQLWSConsumer` themselves either
      gets per-event masking or is documented as not getting it. The seam is installed by
      `consumers.py::build_revalidating_consumer_class`, which only the package router builds,
      so this is the same boundary the operation-stop protocol already has and the same reason
      the package router is the supported mount.
- [ ] The subscription masking rows run at the **live** tier. They are consumer-tier in
      `tests/test_routers.py` today because `examples/fakeshop` has no subscription app and the
      live tier cannot reach a WebSocket through `django.test.Client`; a fakeshop subscription
      surface is its own card.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[feedback2]: ../feedback2.md
[glossary-async-sql-capture-boundary]: ../GLOSSARY.md#async-sql-capture-boundary
[glossary-bounded-query-log-rollover]: ../GLOSSARY.md#bounded-query-log-rollover
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-debug-exception-row]: ../GLOSSARY.md#debug-exception-row
[glossary-debug-payload-availability]: ../GLOSSARY.md#debug-payload-availability
[glossary-debug-sql-row]: ../GLOSSARY.md#debug-sql-row
[glossary-debug-toolbar-middleware]: ../GLOSSARY.md#debug-toolbar-middleware
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-developer-only-debug-posture]: ../GLOSSARY.md#developer-only-debug-posture
[glossary-django-debug-cursor-capture]: ../GLOSSARY.md#django-debug-cursor-capture
[glossary-djangodebugextension]: ../GLOSSARY.md#djangodebugextension
[glossary-djangoerrorpolicyextension]: ../GLOSSARY.md#djangoerrorpolicyextension
[glossary-djangofilepathtype]: ../GLOSSARY.md#djangofilepathtype
[glossary-djangofiletype]: ../GLOSSARY.md#djangofiletype
[glossary-djangoimagepathtype]: ../GLOSSARY.md#djangoimagepathtype
[glossary-djangoimagetype]: ../GLOSSARY.md#djangoimagetype
[glossary-djangomodelformmutation]: ../GLOSSARY.md#djangomodelformmutation
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangoresourcepolicyextension]: ../GLOSSARY.md#djangoresourcepolicyextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-errorpolicy]: ../GLOSSARY.md#errorpolicy
[glossary-execution-resource-policy]: ../GLOSSARY.md#execution-resource-policy
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-graphene-debug-migration]: ../GLOSSARY.md#graphene-debug-migration
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: ../GLOSSARY.md#live-first-coverage-mandate
[glossary-masking-extension-ordering]: ../GLOSSARY.md#masking-extension-ordering
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metafilesystem_path_fields]: ../GLOSSARY.md#metafilesystem_path_fields
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metanullable_overrides]: ../GLOSSARY.md#metanullable_overrides
[glossary-metarequired_overrides]: ../GLOSSARY.md#metarequired_overrides
[glossary-per-field-permission-hooks]: ../GLOSSARY.md#per-field-permission-hooks
[glossary-per-operation-extension-isolation]: ../GLOSSARY.md#per-operation-extension-isolation
[glossary-probe-urlconf]: ../GLOSSARY.md#probe-urlconf
[glossary-reference-counted-cursor-coordinator]: ../GLOSSARY.md#reference-counted-cursor-coordinator
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-request_from_info]: ../GLOSSARY.md#request_from_info
[glossary-resourcepolicy]: ../GLOSSARY.md#resourcepolicy
[glossary-response-extension-merge-semantics]: ../GLOSSARY.md#response-extension-merge-semantics
[glossary-response-extensions-debug-middleware]: ../GLOSSARY.md#response-extensions-debug-middleware
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-schema-audit]: ../GLOSSARY.md#schema-audit
[glossary-seed_data]: ../GLOSSARY.md#seed_data
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-single-upstream-parity]: ../GLOSSARY.md#single-upstream-parity
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[glossary-strawberry-extension-lifecycle]: ../GLOSSARY.md#strawberry-extension-lifecycle
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[rationale]: appx/spec-048-secure_output_defaults-0_0_14-rationale.md
[spec-046]: spec-046-transport_security-0_0_14.md
[spec-047]: spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
