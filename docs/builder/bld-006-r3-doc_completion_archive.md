# Build: R3 — Finish the documentation and audit the archive

Spec reference: `docs/SPECS/spec-006-public_surface-0_0_3.md` (whole file, 168 lines — a discipline spec with no `## Slice checklist`, so this artifact carries a `### Dispatched findings checklist` per `BUILD.md` `### Dispatched findings checklist`)
Status: final-accepted

R3 is the one item of this cycle that runs the **full unmodified worker chain**: Worker 1 plans (this pass), Worker 2 performs the DB edits and the regenerates, Worker 3 reviews, Worker 1 final-verifies. Deviation 2 in `docs/builder/build-006-public_surface-0_0_3.md` removes Worker 2 from R1 and R2 only; Maintainer decision 2 gives R3 real DB work, so nothing here is Worker-1-exclusive except this plan and the final verification.

Everything below was measured on 2026-08-14 at HEAD `947f7494` (re-derived: `git rev-parse --short HEAD` → `947f7494`). Line numbers in generated files (`docs/GLOSSARY.md`, `KANBAN.md`) are pin-at-write-time hints only — **every write below is anchored on an exact unique substring, never on a line number**, because a concurrent card-wrap is writing the same DB and the same two rendered files.

## Plan (Worker 1)

### Spec status / header-line re-verification (mandatory every spawn)

`worker-1.md` `## Spec status-line re-verification` runs at the start of every Worker 1 spawn. Read lines 1-9 of `docs/SPECS/spec-006-public_surface-0_0_3.md`:

- Line 1 is the title. Line 3 is the rationale pointer R1 installed (`Deliberation and this spec's change record live in its companion [rationale file][spec-006-rationale]: …`), which resolves — `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` exists, is the target of the `spec-006-rationale` definition at `:154`, and that definition resolves on disk.
- **The spec carries no `Status:` / target-release / owner / predecessor header line at all**, and never did; `## Problem statement` opens at `:5`. So there is no status line for this pass to falsify or correct. Recorded rather than omitted, because "no header block" is the measurement and silence would read as "not checked".
- No sentence in the first nine lines makes a not-yet-shipped or remains-to-be claim (`grep -nE 'not yet|remains to be|will be shipped' docs/SPECS/spec-006-public_surface-0_0_3.md` → no match).

**No spec edit is owed by this re-verification, and R3 has no licence to make one.** Anything this planning pass discovers about the spec is recorded under `### Notes for Worker 1 (spec reconciliation)` for my own final-verification pass, per the dispatch.

### The split question, answered in writing

`BUILD.md` `### Slice splitting` and `worker-1.md` `### Boundary count is a split trigger` require the answer, not the split.

- **New boundary count: zero.** R3 writes no executable code — three `CardItem.text` values, one `BoardDoc.body`, three regenerates, and read-only sweeps. There is no guard, cap, rejection path, or validation branch to enumerate, so the boundary trigger cannot fire.
- **Diff shape:** one binary DB row-set change plus three generated files whose diff is bounded by the five glossary bullets and three board bullets the plan fixes exactly. Reviewable as one diff.
- **Answer: do not split.** The eight deliverables are one unit because they share one mechanism (edit the DB through the ORM, then regenerate) and one verification instrument (the baseline-regenerate-to-temp diff taken before any write). Splitting them would take that baseline twice against a DB a concurrent session is writing between the two takings — the split would *reduce* verifiability, which is the one outcome the trigger exists to prevent.

### Declarations

- **Hot path: none.** Nothing R3 touches runs per request, per resolver, per row, per connection, or per outbound message. The three renderers are build scripts; the ORM writes are one-shot. `BUILD.md` `## Hot-path budget` therefore owes no number, and Worker 2 writes `Not applicable; plan declares no hot path.`
- **Floor-verification scope: none.** No Django / Strawberry / channels integration seam is touched — no source, no tests, no schema construction. Worker 2 writes `Not applicable; plan declares floor-verification scope none.`
- **Failability proofs: not applicable.** No new boundary and no executable code, so `BUILD.md` `### What needs a proof, and what does not` excludes this item entirely. Worker 2 writes `None; this pass introduced no new boundary.` **Keep the heading either way.**
- **Fail-open shapes: none possible.** There is no expression, clamp, `getattr` default, `or` fallback, or `except` in this item's diff to carry one.
- **Ownership partition: none; sequential residual items** (the plan's own declaration). R3 is the only item in flight.

### DRY analysis

- **Helper inventory checked — for the whole package.** Refreshed this pass with the exact AST inventory in `worker-1.md` `### Package-wide helper inventory before helper planning`, run over all of `django_strawberry_framework/` (not `utils/` alone) with output to a scratch path **outside** the repo (`/tmp/dsf-r3-helper-inventory.md`, 1,782 lines; `docs/shadow/` was deliberately not written because it is not in this pass's authorized writable set). Greped for the shapes this item could conceivably need — `render`, `glossary`, `kanban`, `bullet`, `markdown`, `board` — which matched **17 lines, none of them a candidate**: every hit is error-message rendering (`describe_value`, `DjangoStrawberryFrameworkError.__str__`), SQL rendering (`keyset_seek_sql`), or the schema-export command's GraphQL-string rendering. **No candidate found, and none needed: this item adds no Python.** The reusable machinery it does need lives in `scripts/`, outside the package — `scripts/_kanban_lib.py::configure_django` (which is also what installs the SQLite `busy_timeout` a concurrent writer makes load-bearing) and the three renderers. The plan **reuses all four and writes no new script.**
- **Existing patterns reused.** `scripts/_kanban_lib.py::configure_django` for every ORM step (never a hand-rolled `django.setup()` — the settings module is `config.settings`, not `fakeshop.settings`, and the `busy_timeout` only exists on this path); `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py` for the renders, each of which accepts `--md` / `--html` and `--check`, which is what makes the baseline-to-temp verification possible without touching the tracked files; `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py` for the link reconciliation. In-file bullet patterns reused rather than invented: `- [\`Name\`](#anchor) — gloss.` for a linked name, and the two established exceptions — a bullet whose name is a plain code span with the entry linked from its gloss (`global_id_for` / `decode_global_id` at `docs/GLOSSARY.md:74`), and many bullets pointing at one anchor (`RESOURCE_LIMIT_ERROR_CODE` and `ResourceLimitExceeded` both → `#djangoresourcepolicyextension`; `aapply_cascade_permissions` → `#apply_cascade_permissions`, "shares the entry").
- **New helpers justified: none.** No new script, constant, or helper. If a future cycle needs the roster-vs-bullets comparison a third time, the condition that would justify extracting it is a third caller — card 052's scope already carries "promote a spec/rationale consistency checker into `scripts/`", which is the right home for it, and pre-empting that here would author the second copy of a tool that card is scoped to design.
- **Duplication risk avoided — this is the live DRY question for R3, and it is about prose, not code.** The glossary's convention for a `## Public exports` bullet is a **one-line gloss**, not a second contract: the entry behind the anchor owns the contract. A naive fix would restate what `#errorpolicy` / `#resourcepolicy` / `#production-error-policy` / `#execution-resource-policy` / `#djangomutation` / `#joint-version-cut` already say — which is exactly the defect this cycle has produced four times (a corrected claim reproduced instead of named). Prevention is built into the five bullet texts in `### Implementation steps` step 4: each names **one** distinguishing fact and points at the entry for the rest. Measured guard for Worker 3: the five bullet texts are **158 / 170 / 313 / 357 / 128** characters (measured, in the order the table below lists them), against a longest existing bullet of **267** in the root group (`SerializerMutation`) and **337** across the whole section (the `global_id_for` / `decode_global_id` bullet, which is also the unlinked-name precedent). So four of the five sit inside the root group's existing range and the fifth (357, `DjangoSchema`) is 20 characters past the section's longest — the one bullet covering a class with no entry of its own, and the only length Worker 3 need weigh. None of the five states a precedence order, a default value, a bound, or a validation rule: those are the linked entries'.
- **The one accepted near-duplication, recorded so it is not "fixed".** The existing `ErrorPolicy` and `ResourcePolicy` bullets each end "exported alongside `DEFAULT_ERROR_POLICY`" / "`DEFAULT_RESOURCE_POLICY`". After R3 those names also carry bullets of their own, so the clause reads as a pointer to a sibling bullet. **Leave both existing bullets byte-unchanged.** The clause states the export *pairing*, which is a real fact and the reason the two names ship together, and the plan's scope boundary (`### Maintainer decision 2`, "R3 adds the missing Public-exports bullets … and nothing else") does not authorize editing them.

### Implementation steps

Worker 2 executes these in order. **Every command runs from the repository root.** Steps 1-3 must complete before any write; step 3's baseline is the only instrument that can separate the concurrent card-wrap's pending state from this cycle's output, and it is unrecoverable once a write has landed.

#### Step 1 — Record the starting state, and prove HEAD

```shell
git rev-parse --short HEAD
git status --short
```

Record both verbatim in the build report. Expected baseline-dirty set at plan time (the plan's `## Baseline-dirty out-of-scope files` plus its four growth events): `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3` (the card-wrap); `django_strawberry_framework/_boundary_ordering.py`, `django_strawberry_framework/middleware/request_body.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py` (the transport session); five deleted `docs/review/rev-*.md` plus untracked `docs/review/rev-_boundary_ordering.md` / `review-0_0_14.md`; the spec-007 cycle's files; this cycle's own four dirty/untracked durable paths. **Anything else is a fifth growth event: report it, never revert it, never `git checkout` it.**

#### Step 2 — Take the DB semantic baseline (`iterdump()`, never file bytes)

```shell
mkdir -p /tmp/dsf-r3-baseline
uv run python - <<'PY' > /tmp/dsf-r3-baseline/db-before.sql
import sqlite3
conn = sqlite3.connect("file:examples/fakeshop/db.sqlite3?mode=ro", uri=True)
for line in conn.iterdump():
    print(line)
PY
wc -l /tmp/dsf-r3-baseline/db-before.sql
```

Read-only URI open, so the baseline cannot itself churn the file. `BUILD.md` `### Tracked binary / generated files` is explicit that a same-size binary diff is **not** proof of a no-op and that the comparison is the `iterdump()`, not the bytes.

#### Step 3 — Take the regenerate-to-temp baseline, BEFORE any DB edit

```shell
uv run python scripts/build_kanban_md.py   --md /tmp/dsf-r3-baseline/KANBAN.md
cp KANBAN.html /tmp/dsf-r3-baseline/KANBAN.html
uv run python scripts/build_kanban_html.py --html /tmp/dsf-r3-baseline/KANBAN.html
uv run python scripts/build_glossary_md.py --md /tmp/dsf-r3-baseline/GLOSSARY.md
diff /tmp/dsf-r3-baseline/KANBAN.md   KANBAN.md        | head -40
diff /tmp/dsf-r3-baseline/KANBAN.html KANBAN.html      | head -40
diff /tmp/dsf-r3-baseline/GLOSSARY.md docs/GLOSSARY.md | head -40
```

- **`KANBAN.html` needs the `cp` first**: `build_kanban_html.py` *embeds* a data block into an existing shell, and the Vue shell is hand-edited (`START.md` "Rendered docs"). Pointing `--html` at a non-existent path is not a render.
- These three diffs are **the concurrent writer's pending state**: whatever the working-tree files carry that a fresh render of the current DB does not. Record each verbatim (or "empty") in the build report. They are the subtrahend for step 9.

#### Step 4 — Close the `## Public exports` roster gap (Maintainer decision 2)

**The section is ONE `BoardDoc` row, not a set of `GlossaryTerm` rows**: `apps.kanban.models.BoardDoc`, **pk 41**, `namespace='glossary'`, `key='public-exports'`, `title='Public exports'`, `kind='Glossary'`, `order=2`, `include_heading=True`, `body` 7,843 bytes / 58 lines. The rendered markdown *is* that `body`. Do not go looking for per-term rows; there are none for these bullets.

**The gap, re-derived this pass rather than inherited** (`uv run python` over `__init__.py`'s `__all__` and the body's root group): `__all__` carries **37** names; the root re-export group carries **34** bullets; **33** of those 34 are `__all__` names and the 34th is `SerializerMutation`, which is deliberately outside `__all__` while DRF is a soft dependency. 37 − 33 = **4** names with no bullet: `DEFAULT_ERROR_POLICY`, `DEFAULT_RESOURCE_POLICY`, `DjangoMutationExecutionContext`, `DjangoSchema`. R2's final verification added a **fifth** site: `__version__` has a bullet with **no link and no marker**, so condition 3 at `spec:44` fails it. That is 34 → 38 bullets in the root group and 44 → 48 in the section.

**Order.** The root group sorts case-insensitively on the name (`OptimizerHint` < `RESOURCE_LIMIT_ERROR_CODE` < `ResourceLimitExceeded` < `ResourcePolicy` is only consistent under a case-folded ASCII sort), with three standing exceptions that are **not** to be "fixed": `DjangoType` sits between `DjangoNodesField` and `DjangoOptimizerExtension`; `aapply_cascade_permissions` follows `apply_cascade_permissions` because it shares its entry; `auto` and `__version__` close the group. Each insertion below therefore lands where the case-folded sort puts it.

**The five dispositions, decided here so Worker 2 writes rather than judges.** Every anchor named below exists today and its entry carries `**Status:** shipped (…)`, which is what `spec:44` condition 3 reads (verified: `#errorpolicy` shipped `0.0.14`, `#resourcepolicy` `0.0.14`, `#production-error-policy` `0.0.14`, `#execution-resource-policy` `0.0.14`, `#djangomutation` `0.0.11`, `#joint-version-cut` `0.0.13`).

| # | Name | Position | Anchor, or the reason it is unlinked |
|---|---|---|---|
| 1 | `DEFAULT_ERROR_POLICY` | immediately after the `BigInt` bullet (body line 3) | name links `#errorpolicy` — that entry explicitly says the dataclass is "root-exported alongside `DEFAULT_ERROR_POLICY`", so it is the entry that documents this name |
| 2 | `DEFAULT_RESOURCE_POLICY` | immediately after #1 | name links `#resourcepolicy` — same construction, same sentence shape ("root-exported alongside `DEFAULT_RESOURCE_POLICY`") |
| 3 | `DjangoMutationExecutionContext` | between the `DjangoMutation` and `DjangoMutationField` bullets | **name unlinked**, following the `global_id_for` / `decode_global_id` precedent at `docs/GLOSSARY.md:74` (a plain code span whose gloss carries the pointer): no glossary entry documents the mutation-transaction window, so no anchor can honestly host the name. The gloss links `#djangomutation`, the entry for the write pipeline it wraps, as a true "see" pointer rather than a false definition. Authoring an entry is entry-granularity work, which `### Maintainer decision 2` assigns to card 052 |
| 4 | `DjangoSchema` | immediately after the `DjangoResourcePolicyExtension` bullet (last of the `Django*` run, before `ErrorPolicy`) | **name unlinked**, same precedent and same reason — there is no `#djangoschema` anchor, card 047's closeout deliberately removed the dangling links rather than authoring the entry, and whether the entry should exist is card 052's open decision. The gloss links the two entries that *do* document what `DjangoSchema` does at construction: `#production-error-policy` and `#execution-resource-policy` |
| 5 | `__version__` | **stays exactly where it is**, last in the group; only its text changes | name links `#joint-version-cut` — R2's conditional route resolves to its **first** branch, not the card-052 fallback. That entry names `__version__` explicitly as one of the five members of the version quintet moved only by the joint cut, and carries `**Status:** shipped (0.0.13)`. So `__version__` gains a marker without authoring anything, `spec:44` is not weakened, and **nothing about `__version__` goes onto card 052** |

**The exact bullet texts.** Write these character-for-character (Worker 3 diffs them against this plan). Em dashes are correct here — the ASCII-only rule is `.py`-only, and the surrounding root-group bullets all use `—`.

```text
- [`DEFAULT_ERROR_POLICY`](#errorpolicy) — the all-defaults `ErrorPolicy` instance; what error-policy resolution returns when a deployment configures nothing.
```

```text
- [`DEFAULT_RESOURCE_POLICY`](#resourcepolicy) — the all-defaults `ResourcePolicy` instance; what resource-policy resolution returns when a deployment configures nothing.
```

```text
- `DjangoMutationExecutionContext` — the graphql-core `ExecutionContext` subclass `DjangoSchema` installs by default, which holds each top-level generated mutation's transaction open until graphql-core has finished completing that field's value. The write pipeline it wraps is [`DjangoMutation`](#djangomutation).
```

```text
- `DjangoSchema` — the `strawberry.Schema` subclass required for any schema exposing generated mutations: it resolves the [production error policy](#production-error-policy) and the [execution resource policy](#execution-resource-policy) once at construction, installs their extensions, and runs generated mutations through `DjangoMutationExecutionContext`.
```

```text
- [`__version__`](#joint-version-cut) — package version string; part of the version quintet moved only by the joint version cut.
```

Every factual clause above was verified against source this pass: `kwargs.setdefault("execution_context_class", DjangoMutationExecutionContext)` in `django_strawberry_framework/schema.py::DjangoSchema.__init__`; "The REQUIRED schema class for any schema exposing generated mutations" in that class's docstring; `DEFAULT_ERROR_POLICY = ErrorPolicy()` plus `resolve_error_policy`'s `if overrides is None: return DEFAULT_ERROR_POLICY` in `error_policy.py`, and the same shape in `resource_policy.py`; the transaction-window description in `schema.py`'s module docstring.

**The ORM write.** Anchored on unique substrings, with the uniqueness asserted before the write, and `.save()` so the `post_save` hook creates the `UUIDModel` side-row the renderers query. A raw SQL `UPDATE` skips that hook and breaks the render.

```shell
uv run python - <<'PY'
import sys
sys.path.insert(0, "scripts")
from _kanban_lib import configure_django
configure_django()
from apps.kanban.models import BoardDoc

doc = BoardDoc.objects.get(pk=41)
assert (doc.namespace, doc.key) == ("glossary", "public-exports"), (doc.namespace, doc.key)
body = doc.body
before = len(body)

EDITS = [
    # (anchor, replacement) -- each anchor must occur exactly once
    (
        "- [`BigInt`](#bigint-scalar) — JSON-safe scalar for 64-bit integer fields.\n",
        "- [`BigInt`](#bigint-scalar) — JSON-safe scalar for 64-bit integer fields.\n"
        "- [`DEFAULT_ERROR_POLICY`](#errorpolicy) — the all-defaults `ErrorPolicy` instance;"
        " what error-policy resolution returns when a deployment configures nothing.\n"
        "- [`DEFAULT_RESOURCE_POLICY`](#resourcepolicy) — the all-defaults `ResourcePolicy`"
        " instance; what resource-policy resolution returns when a deployment configures"
        " nothing.\n",
    ),
    (
        "- [`DjangoMutationField`](#djangomutationfield)",
        "- `DjangoMutationExecutionContext` — the graphql-core `ExecutionContext` subclass"
        " `DjangoSchema` installs by default, which holds each top-level generated mutation's"
        " transaction open until graphql-core has finished completing that field's value."
        " The write pipeline it wraps is [`DjangoMutation`](#djangomutation).\n"
        "- [`DjangoMutationField`](#djangomutationfield)",
    ),
    (
        "- [`ErrorPolicy`](#errorpolicy)",
        "- `DjangoSchema` — the `strawberry.Schema` subclass required for any schema exposing"
        " generated mutations: it resolves the [production error policy]"
        "(#production-error-policy) and the [execution resource policy]"
        "(#execution-resource-policy) once at construction, installs their extensions, and runs"
        " generated mutations through `DjangoMutationExecutionContext`.\n"
        "- [`ErrorPolicy`](#errorpolicy)",
    ),
    (
        "- `__version__` — package version string.",
        "- [`__version__`](#joint-version-cut) — package version string; part of the version"
        " quintet moved only by the joint version cut.",
    ),
]
for anchor, replacement in EDITS:
    assert body.count(anchor) == 1, (body.count(anchor), anchor[:60])
    body = body.replace(anchor, replacement, 1)

doc.body = body
doc.save()
print("body bytes", before, "->", len(doc.body))
PY
```

Note the string concatenations above must produce the five bullet texts **exactly** as fenced earlier — Worker 2 verifies that by re-reading `BoardDoc.objects.get(pk=41).body` and diffing the five lines against this plan, not by trusting the concatenation.

#### Step 5 — Discharge the card-052 prose (retirement rows 8 and 9, plus the one clause R3's own step 4 falsifies)

Three `CardItem` rows, all on `Card.objects.get(number=52)` (`TODO-ALPHA-052-0.1.0`, status `todo`), all in section `scope`, all `is_complete=False`. **Do not tick `is_complete` on any of them** — card 052 carries far more than these clauses, and the tick is not R3's to make.

**Row 8 — `CardItem` pk 1260** (order 8, 1,264 chars, rendered at `KANBAN.md:319`). Every clause of it is discharged, and the discharge was re-verified mechanically this pass rather than read from R2's report: `grep -oiE 'visibility[ -]status'` counts **0** occurrences in `docs/SPECS/spec-002-optimizer-0_0_2.md` and **0** in `docs/SPECS/spec-006-public_surface-0_0_3.md`; `grep -n 'spec-002-visibility'` in `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` returns nothing (the link definition is gone); that companion's removed-`## Current state` entry now names `[Shipped slices][spec-002-shipped]` as what absorbed the content; and the appended record exists as `## The discharged deferral — Visibility status retired by the spec-006 cycle` at `:503`. spec-002's headings are now `Purpose` / `Problem statement` / `Architecture decision` / `Shipped slices` / `Coordination with spec-001…` / `References` / `Implementation checklist` — **no status-shaped section survives.**

Replacement text (the closing spec-003 sentence is **live and survives verbatim**; the spec-002-residual-cycle sentence is still true and survives verbatim; note the item's house style uses a spaced ASCII hyphen ` - ` as its dash, not an em dash — keep it):

```text
`docs/SPECS/spec-002-optimizer-0_0_2.md` carries no status-shaped section any more. The spec-002 residual cycle discharged most of them - `## Open questions` and `## Current state` are gone, and `## Shipped slices` and `## Implementation checklist` survive the argument on their merits, since a past-tense fact about what shipped is not a promise about the present. The last one, `## Visibility status`, was retired by the spec-006 residual cycle as a cross-spec duplicate under the single-ownership law: the section existed because `spec-006-public_surface-0_0_3.md` asked for a copy, and both of spec-006's citing bullets were retired with it, so nothing in spec-006 names the section. The companion `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` no longer defines a `#visibility-status` link target either, and the sentence that used it now names `## Shipped slices` as what absorbed the removed content; the discharge and its reasoning are recorded in that companion's `## The discharged deferral - Visibility status retired by the spec-006 cycle`. `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` no longer carries its when-O4-ships instruction at all - the 2026-08-07 reconciliation deleted the section - so nothing in spec-003 names these headings any more.
```

**Row 9 — `CardItem` pk 1270** (order 11, 1,150 chars, rendered at `KANBAN.md:322`). Only the **final sentence** is falsified. Everything before it — the whole live spec-003 divergence this card must settle — survives byte-identically. Replace only:

```text
 Do not sweep up `spec-006-public_surface-0_0_3.md:136` and `:147` in the same pass: both name `## Visibility status`, and both are live and correct.
```

with:

```text
 The prior instruction not to sweep up spec-006's two citations of `## Visibility status` is spent: the spec-006 residual cycle retired both bullets with the heading they named, so nothing in spec-006 references the section.
```

The two raw `path:NN` refs are deliberately **not** carried into the new sentence: they no longer resolve (the reconciled spec is 168 lines), and `AGENTS.md` rule 27 keeps raw `path:NN` out of standing docs, which `KANBAN.md` is. Naming the sites descriptively loses nothing a reader can use.

**The third row — `CardItem` pk 1240** (order 1, 525 chars, rendered at `KANBAN.md:314`). This one is **not** a retirement site; it is the site R3's *own* step 4 falsifies. Its first sentence currently ends "…and `DjangoSchema` / `DjangoMutationExecutionContext` are absent from the Public exports list even though both are in `__all__`" — false the moment step 4 lands. Leaving it would publish, on the board, the exact gap this cycle just closed, and would recreate D13 (the root cause: nothing folded back). The fix is a **single-sentence** surgery; the rest of the item — the `#djangoschema` history, card 047's closeout, and the still-open entry question — is correct and survives verbatim. Replace only:

```text
`docs/GLOSSARY.md` has no `DjangoSchema` entry, so the schema constructor's two policy arguments are described only from the `ErrorPolicy` / `ResourcePolicy` side, and `DjangoSchema` / `DjangoMutationExecutionContext` are absent from the Public exports list even though both are in `__all__`.
```

with:

```text
`docs/GLOSSARY.md` has no `DjangoSchema` entry, so the schema constructor's two policy arguments are described only from the `ErrorPolicy` / `ResourcePolicy` side. The spec-006 residual cycle closed the roster half: `DjangoSchema` and `DjangoMutationExecutionContext` now carry Public-exports bullets whose glosses link the entries that describe them, so what remains open is only whether either name earns an entry and anchor of its own.
```

**Authorization for the third row, stated rather than assumed.** It is a widening of the dispatch's deliverable 2 by one `CardItem`, and it is licensed by three things the cycle already declares: `## The single-ownership law` clause 2 ("fixes every inbound reference in the same change" — the maintainer's own "since we did not fix every inbound reference in the same change last time, do that now"); `### Maintainer decision 2`, which cites this very item as the record of the gap it closes; and the fact that the falsification is **caused by this pass**, which makes it a defect rather than a deferral. It stays inside the same card, the same section, and the same subject as rows 8/9, and touches no other file. **If Worker 3 or the maintainer judges it out of scope, the fallback is to revert this one row's text and record the falsified clause as a card-052 sweep item — but the plan's decided position is to fix it, because a board claim knowingly falsified by this cycle's own write is not a deferral.**

**The ORM write for all three rows:**

```shell
uv run python - <<'PY'
import sys
sys.path.insert(0, "scripts")
from _kanban_lib import configure_django
configure_django()
from apps.kanban.models import CardItem

# (pk, anchor-substring, replacement) -- anchor must occur exactly once in .text
PLAN = [
    (1260, "<the whole current text>", "<the row-8 replacement above>"),
    (1270, "<the final sentence above>", "<its replacement above>"),
    (1240, "<the first sentence above>", "<its replacement above>"),
]
for pk, anchor, replacement in PLAN:
    item = CardItem.objects.get(pk=pk)
    assert item.card.card_id == "TODO-ALPHA-052-0.1.0", item.card.card_id
    assert item.section.key == "scope", item.section.key
    assert item.text.count(anchor) == 1, (pk, item.text.count(anchor))
    item.text = item.text.replace(anchor, replacement, 1)
    assert item.is_complete is False
    item.save()          # .save(), never queryset .update() -- post_save owns the side-row
    print(pk, "ok", len(item.text))
PY
```

For pk 1260 the whole text is replaced, so the anchor is the full current text (fetch it, assert it matches the text quoted above, then assign). For pk 1270 and pk 1240 the anchor is the single sentence quoted above, leading space included where shown.

#### Step 6 — Re-run `import_spec_terms`, writing form first

Only the read-only `--check` form has been invoked in this cycle. Run the **writing** form now, and run it **before** the regenerates in step 7:

```shell
uv run python examples/fakeshop/manage.py import_spec_terms
uv run python examples/fakeshop/manage.py import_spec_terms --check
```

- **Why before the regenerates:** the writing form reconciles `GlossarySpecMention` rows and rebuilds each done card's `glossary_links`, and `scripts/build_kanban_md.py::render_glossary_terms` renders those links into `KANBAN.md`'s per-card `#### Glossary terms` tables. A regenerate that ran first would miss any change. (Measured counterweight, so nobody misreads it: `allGlossarySpecMentions` is fetched by `scripts/build_glossary_md.py` but used only for its CLI summary line — mentions do **not** render into `docs/GLOSSARY.md`'s body.)
- **Its DB diff legitimately spans more than card 6.** The command walks **every** done card and reconciles mentions for all of them; a wider `iterdump()` diff than card `DONE-006-0.0.3` is expected output, not a defect. Say so in the build report so no later pass reads it as one.
- `--check` afterwards must print `OK: 49 done cards have glossary links.` and exit 0. A different count is a stop-and-report, not something to "fix".

#### Step 7 — Regenerate all three docs, then prove byte-stability

```shell
uv run python scripts/build_kanban_md.py
uv run python scripts/build_kanban_html.py
uv run python scripts/build_glossary_md.py
cp KANBAN.md /tmp/dsf-r3-baseline/KANBAN.md.pass1
cp KANBAN.html /tmp/dsf-r3-baseline/KANBAN.html.pass1
cp docs/GLOSSARY.md /tmp/dsf-r3-baseline/GLOSSARY.md.pass1
uv run python scripts/build_kanban_md.py
uv run python scripts/build_kanban_html.py
uv run python scripts/build_glossary_md.py
cmp KANBAN.md        /tmp/dsf-r3-baseline/KANBAN.md.pass1
cmp KANBAN.html      /tmp/dsf-r3-baseline/KANBAN.html.pass1
cmp docs/GLOSSARY.md /tmp/dsf-r3-baseline/GLOSSARY.md.pass1
uv run python scripts/build_kanban_md.py   --check
uv run python scripts/build_kanban_html.py --check
uv run python scripts/build_glossary_md.py --check
```

Three `cmp` exit-0 results are the **two-consecutive-regenerate byte-stability** proof; the three `--check` exit-0 results are its independent confirmation. **Never hand-edit any of the three files** — the next render silently reverts a hand edit (`START.md` "Rendered docs — fix the source, not the file"; `AGENTS.md` #"GLOSSARY.md is DB-generated").

Also run the scaffold gate in **`--check`** mode only (its default is auto-fix, which on a generated file is a hand edit by another name):

```shell
uv run python scripts/check_trailing_commas.py --check KANBAN.md docs/GLOSSARY.md
```

#### Step 8 — Spot-check the rendered result

Byte-stability proves determinism, not correctness. Re-derive the roster arithmetic **from the rendered file**:

```shell
uv run python - <<'PY'
import pathlib, re
pkg = pathlib.Path("django_strawberry_framework/__init__.py").read_text()
names = re.findall(r'"([^"]+)"', re.search(r"__all__\s*=\s*\((.*?)\)\n", pkg, re.S).group(1))
lines = pathlib.Path("docs/GLOSSARY.md").read_text().splitlines()
start = lines.index("Symbols re-exported from `django_strawberry_framework`:") + 2
end = next(i for i in range(start, len(lines)) if not lines[i].startswith("- "))
group = lines[start:end]
bullets = [re.match(r"- \[?`([^`]+)`", line).group(1) for line in group]
print("__all__", len(names), "| root bullets", len(bullets))
print("missing bullets:", [n for n in names if n not in bullets])
print("bullets not in __all__:", [b for b in bullets if b not in names])
print("unlinked bullets in the whole section:")
sec = lines[lines.index("## Public exports"):]
sec = sec[: next(i for i in range(1, len(sec)) if sec[i].startswith("## "))]
print([l[:44] for l in sec if l.startswith("- ") and "](#" not in l])
PY
```

Expected: `__all__ 37 | root bullets 38`; `missing bullets: []`; `bullets not in __all__: ['SerializerMutation']`; and **`unlinked bullets: []`** — before this pass exactly one of the section's 44 bullets carried no link at all (`__version__`); after it, all 48 carry one. That last line is the cleanest single re-derivable statement that condition 3 at `spec:44` now holds for every `__all__` name.

Then read, by eye, in `docs/GLOSSARY.md`: the five new/changed bullets sit at the positions the table in step 4 prescribes; the four group lead-in sentences are intact and in order (root roster, `extensions`, `testing`, `auth`) — R2's `spec:17`, `:44` and `:76` all rest on that shape; `## Status legend` still carries all five markers including `alpha constraint`, and still renders **before** `## Public exports`; the `SerializerMutation` bullet still says why it is outside `__all__`; and no group listing was added for `views` / `routers` / `middleware.debug_toolbar` (**card 052's, explicitly not R3's** — the plan's `CORRECTION`).

In `KANBAN.md`: the three rewritten card-052 bullets render as one bullet each in the `#### Scope` list, in their original order positions (1, 8, 11), with no stray markdown; card `DONE-006-0.0.3`'s `#### Glossary terms` table still lists 7 rows; and no other card's text moved.

#### Step 9 — Classify the diff, and hand the mixed diff to the maintainer

```shell
git status --short
diff /tmp/dsf-r3-baseline/GLOSSARY.md docs/GLOSSARY.md
diff /tmp/dsf-r3-baseline/KANBAN.md   KANBAN.md
diff /tmp/dsf-r3-baseline/KANBAN.html KANBAN.html
uv run python - <<'PY' > /tmp/dsf-r3-baseline/db-after.sql
import sqlite3
conn = sqlite3.connect("file:examples/fakeshop/db.sqlite3?mode=ro", uri=True)
for line in conn.iterdump():
    print(line)
PY
diff /tmp/dsf-r3-baseline/db-before.sql /tmp/dsf-r3-baseline/db-after.sql | head -60
```

**This is the acceptance criterion, and it is why step 3 could not be skipped.** The three `diff`s against the step-3 baselines must show **only** this cycle's own output: five bullet lines in `docs/GLOSSARY.md`, three bullet lines in `KANBAN.md`, and the corresponding data-block change in `KANBAN.html`. "`git diff` is clean" is available as a verification for **none** of the four paths — all four are baseline-dirty from the concurrent card-wrap. If a baseline diff shows more, classify every extra line: a concurrent writer's row is **reported, never reverted** (`AGENTS.md` rule 34), and `git checkout` is banned outright.

The `iterdump()` diff must reduce to: the four rows this pass wrote (`BoardDoc` 41, `CardItem` 1240 / 1260 / 1270, plus their `modified` timestamps and any `UUIDModel` side-row), the `GlossarySpecMention` / card-link reconciliation from step 6, and whatever the concurrent card-wrap landed in between. Name which is which.

Finally, prove this cycle's work was not swept into another session's commit — with `git log --stat`, never `git status`:

```shell
git rev-parse --short HEAD
git log --stat -3 -- docs/GLOSSARY.md KANBAN.md KANBAN.html examples/fakeshop/db.sqlite3
```

#### Step 10 — The durable-doc audit (READ-AND-REPORT; no edit is authorized)

Confirm `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`, and the root `README.md` describe the public surface and its status vocabulary as the reconciled spec now states them. **No edit to `docs/README.md` or `docs/TREE.md` is authorized** — a concurrent session is editing that neighbourhood and the spec-007 cycle owns `docs/README.md`. Root `README.md` is not in this cycle's writable set either. Everything found goes to the maintainer or onto card 052.

Re-derive, do not trust:

```shell
uv run python - <<'PY'
import ast, pathlib, importlib
pkg = pathlib.Path("django_strawberry_framework/__init__.py").read_text()
pinned = None
for node in ast.walk(ast.parse(pathlib.Path("tests/base/test_init.py").read_text())):
    if isinstance(node, ast.FunctionDef) and node.name == "test_public_api_surface_is_pinned":
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assert) and isinstance(stmt.test, ast.Compare):
                cand = stmt.test.comparators[0]
                if isinstance(cand, ast.Tuple):
                    pinned = tuple(ast.literal_eval(cand))
                    break
live = tuple(ast.literal_eval(ast.parse(pkg).body[[
    isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "__all__"
    for n in ast.parse(pkg).body].index(True)].value))
print("len(__all__)", len(live), "| pin matches", pinned == live)
print("pin-only", set(pinned or ()) - set(live), "| all-only", set(live) - set(pinned or ()))
PY
grep -n '^- `' docs/GLOSSARY.md | sed -n '1,8p'          # the ## Status legend rows
grep -c 'planned by TODO-' docs/TREE.md                  # target-tree card anchoring
grep -n '^#\{2,3\} ' docs/README.md | grep -iE 'current surface|package architecture'
```

Expected at plan time, each re-measurable: `len(__all__)` **37** and the pin **matches** it exactly (the pin is a literal tuple comparison, so this is a token-level identity check, not a count); the legend carries exactly five markers — `shipped`, `planned for X.Y.Z`, `deferred`, `alpha constraint`, `post-1.0.0`; `docs/TREE.md` carries **9** `planned by TODO-` target entries, which is what `spec:87` licenses (naming the card resolves to a release where a bare marker does not); and `docs/README.md` has **no** `## Current surface` and **no** `## Package architecture` section — the two obligations the spec no longer carries and `spec-007` owns. Occurrence counts of the three retired markers across the five durable docs, measured this pass, for Worker 2 to re-take: `experimental` 0/0/0/0/0, `aspirational` 0/0/0/0/0, `in flight` 0 everywhere except one occurrence in `docs/GLOSSARY.md`, which is prose rather than a marker — consistent with the plan's D9 and requiring no correction. `docs/README.md` publishes no per-feature marker of its own; its `## Today and coming next` is a release-scoped summary stamped with one version and points at `docs/GLOSSARY.md` for per-feature status, which is exactly the shape `spec:89` licenses. `docs/TREE.md` references spec-006 zero times.

#### Step 11 — The three-direction cross-reference sweep

```shell
# (a) references TO spec-006
grep -rln 'spec-006' --include='*.md' --include='*.html' . | grep -v '^./.venv' | sort
for f in $(grep -rl 'spec-006' --include='*.md' --include='*.html' . | grep -v '^./.venv'); do \
  printf '%s %s\n' "$(grep -o 'spec-006' "$f" | wc -l | tr -d ' ')" "$f"; done | sort -k2
# (b) references FROM spec-006, and (c) from the rationale at appx/ depth
uv run python - <<'PY'
import pathlib, re
for p in ("docs/SPECS/spec-006-public_surface-0_0_3.md",
          "docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md"):
    path = pathlib.Path(p); txt = path.read_text()
    defs = re.findall(r"^\[([^\]]+)\]:\s*(\S+)\s*$", txt, re.M)
    body = re.sub(r"`[^`]*`", "", txt.split("<!-- LINK DEFINITIONS -->")[0])
    uses = set(re.findall(r"\]\[([^\]]+)\]", body))
    bad = [(k, v) for k, v in defs
           if v.split("#")[0] and not (path.parent / v.split("#")[0]).resolve().is_file()]
    print(p, "| defs", len(defs), "| used ids", len(uses),
          "| unresolved", bad, "| undefined", sorted(uses - {k for k, _ in defs}),
          "| unused", sorted({k for k, _ in defs} - uses))
PY
```

Measured this pass, so Worker 2 re-derives against a target: **the spec has 8 definitions, all 8 used, 0 undefined, 0 unused, all 8 resolving on disk** (7 × `../GLOSSARY.md#…` plus `appx/spec-006-…-rationale.md`); **the rationale has 16 definitions, all 16 used, 0 undefined, 0 unused, all resolving**, and its 12 fragment-bearing definitions all slug to real spec-006 headings (verified with a markup-rendering slugger — `#decision-for-003` for `#### Decision for 0.0.3`, since a dotted version slugs to `003`, not `0_0_3`). Its outbound depth conventions are correct for `docs/SPECS/appx/`: `../../builder/BUILD.md` for a `docs/`-tree target, `../spec-006-….md` for a `docs/SPECS/` sibling, and a bare filename for an `appx/` sibling.

Direction (a) at plan time: `KANBAN.md` (7 occurrences) and `KANBAN.html` (6) — generated, and the only hand-authored source behind them is the DB this cycle writes; `docs/SPECS/spec-005-django_type_contract-0_0_3.md:89` (1) — still the **only** inbound reference from another spec, and R2 settled it by measurement (the by-title citation survives at `spec-006:102`, still inside `### Status-marker vocabulary`, so `:89` is true and `spec-005` was correctly never edited); `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (13) — R2's own output plus the appended discharge record; `docs/SPECS/appx/spec-005-…-rationale.md` (1); prior cycles' build plans and `bld-*` artifacts (`build-001`, `build-002`, `build-005`, `bld-005-*`) — **historical, never edited**. **Two sites are new since the plan's table and both are another session's:** `docs/SPECS/appx/spec-007-…-rationale.md` (6) and `docs/builder/bld-007-r1` / `bld-007-r2` (29 / 10), plus `docs/review/rev-_boundary_ordering.md` (1) and `docs/review/review-0_0_14.md` (2). **Report them; edit none.** The spec-007 cycle owns its own files, and `## The single-ownership law` clause 3 holds — the retirement licence covered `spec-002` and its companion only, and it is spent.

#### Step 12 — The staged-anchor sweep

```shell
grep -rEn 'TODO\(spec-006|TODO-(ALPHA|BETA|STABLE)-006' . | grep -v '^./.venv'
```

Expected: zero hits outside `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` and this cycle's own `bld-006-*` / `build-006-*` artifacts quoting the pattern. `BUILD.md` `## Cross-slice integration pass` step 6 excludes the board files, where `TODO-<MILESTONE>-<NNN>` legitimately names unshipped cards; card 006 is `DONE-006-0.0.3`, so a `TODO-ALPHA-006` form should not appear at all. Report the hit list, classified by file.

#### Step 13 — Verify the archive is complete

```shell
ls -l docs/SPECS/spec-006-public_surface-0_0_3.md \
      docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv \
      docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md
uv run python - <<'PY'
import sys
sys.path.insert(0, "scripts")
from _kanban_lib import configure_django
configure_django()
from apps.kanban.models import Card, SpecDoc
card = Card.objects.get(number=6)
print(card.card_id, card.status.key, card.target_version.number,
      "| glossary_links", card.glossary_links.count())
print("SpecDoc.path", SpecDoc.objects.get(card=card).path)
PY
grep -c '' docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv
grep -n 'spec-006' KANBAN.md
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md
git status --short docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv
```

Expected, all measured this pass: all three files present; `DONE-006-0.0.3 done 0.0.3 | glossary_links 7`; `SpecDoc.path docs/SPECS/spec-006-public_surface-0_0_3.md`; the terms CSV **8 lines** = header + **7** anchor rows, one row per anchor (which is what makes it importable — `worker-0.md` `### DONE-card invariants` is explicit that a green `check_spec_glossary` does not prove the DB-side count, so both are checked); `check_spec_glossary` prints `OK: 7 terms - all have glossary entries and at least one spec link.` and exits 0; and the terms CSV is **absent from `git status`**, i.e. byte-unchanged — it must stay so, since `import_spec_terms` rebuilds card 6's links from it. **R3 verifies all of this; it changes none of it.** No card move, no status flip, no `SpecDoc` repoint, no CSV edit.

The two `KANBAN.md` references to the archived spec (the card-006 body and its predicted-files/spec row) must both still read `docs/SPECS/spec-006-public_surface-0_0_3.md` after the regenerate — they are generated from `SpecDoc.path`, so they follow it by construction; confirm rather than assume, and note that after step 5 the `grep -n 'spec-006' KANBAN.md` hit list also includes the three rewritten card-052 bullets, so the post-write occurrence count is expected to differ from the pre-write 7. Report the number you measure; do not hold a target for it.

### Test additions / updates

**No test is owed, and none may be added.** No package source changes, so `AGENTS.md` "Add tests in the same change as code" has no code to attach a test to, and `## Build-wide context flags` makes every source and test file read-only for this cycle — `tests/base/test_init.py` explicitly included. The verification commands that stand in for a test run, all in `### Implementation steps`:

- `scripts/build_kanban_md.py --check`, `build_kanban_html.py --check`, `build_glossary_md.py --check` (all exit 0) plus three `cmp` results — determinism of the render.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` exit 0 — the card-wrap chain behind `DONE-006-0.0.3`.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` exit 0 — the 7-anchor constraint.
- `uv run python scripts/check_trailing_commas.py --check KANBAN.md docs/GLOSSARY.md` — the `.md` scaffold gate, `--check` only.
- The step-8 roster script — `__all__` 37 vs 38 root bullets, `missing bullets: []`, `unlinked bullets: []`.
- The step-9 baseline diffs and `iterdump()` comparison.

**No `pytest --cov*` in any form**, in any pass (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). No focused `pytest` scope is called for either: nothing in this item's diff is executed by the suite. The final gate runs the full sweep under the plan's recorded baseline exception.

### Implementation discretion items

Assessed and decided to be Worker 2's:

- Whether the ORM edits land as one script or four (one per row plus the `BoardDoc`), and whether the heredocs are inlined or written to a scratch file **outside** the repo. The assertions and the `.save()` requirement are not discretionary; the packaging is.
- The scratch directory name (`/tmp/dsf-r3-baseline/` is a suggestion) — provided it is outside the repository, which is not discretionary.
- Whether the baseline `iterdump()` diff is inspected with `diff`, `comm`, or a Python set difference, provided the report classifies every differing row.

Not discretionary, and not delegated: the five bullet texts, their five positions, the five anchor decisions, the three replacement prose blocks, the step order (baselines → DB → `import_spec_terms` → regenerate), and the read-only status of `docs/README.md` / `docs/TREE.md` / the root `README.md` / all source and tests.

### Dispatched findings checklist

One box per deliverable. Boxes stay `- [ ]` at planning; **Worker 2 ticks each in the same build report that lands it**; Worker 3 walks the list; Worker 1 audits every tick at final verification. This cycle has already produced **four** findings whose substance was right and whose cited evidence was false, so every box below cites evidence a reviewer can re-derive **mechanically** — a command and its expected output, anchored on the shape the box actually claims, counting occurrences rather than matching lines, and naming a model rather than a GraphQL type wherever a DB row is cited.

- [x] **D1 — the four missing roster bullets landed.** `BoardDoc` pk 41 (`apps.kanban.models.BoardDoc`, `namespace='glossary'`, `key='public-exports'`) carries bullets for `DEFAULT_ERROR_POLICY`, `DEFAULT_RESOURCE_POLICY`, `DjangoMutationExecutionContext`, and `DjangoSchema`, at the four positions in `### Implementation steps` step 4's table. Evidence: the step-8 script prints `__all__ 37 | root bullets 38` and `missing bullets: []`.
- [x] **D2 — the `__version__` residue is closed by a link, not a carve-out.** Its bullet links `#joint-version-cut`, whose entry names `__version__` in the version quintet and carries `**Status:** shipped (0.0.13)`. `spec:44` is byte-unchanged. Evidence: the step-8 script prints `unlinked bullets: []` (exactly one bullet was unlinked before this pass), and `git diff -- docs/SPECS/spec-006-public_surface-0_0_3.md` is empty.
- [x] **D3 — retirement row 8 discharged.** `CardItem` pk 1260 (card `TODO-ALPHA-052-0.1.0`, section `scope`, order 8) states that spec-002 carries no status-shaped section, that the spec-006 cycle retired `## Visibility status` as a cross-spec duplicate, and where the discharge is recorded; the closing spec-003 sentence survives verbatim; `is_complete` is still `False`. Evidence: `grep -oiE 'visibility[ -]status' docs/SPECS/spec-002-optimizer-0_0_2.md | wc -l` → `0`, and the same grep over `docs/SPECS/spec-006-public_surface-0_0_3.md` → `0`.
- [x] **D4 — retirement row 9 discharged.** `CardItem` pk 1270 (order 11) no longer instructs a reader not to sweep two spec-006 sites, and carries no raw `path:NN` reference to spec-006; every clause about the live spec-003 divergence survives verbatim; `is_complete` is still `False`. Evidence: `grep -c 'public_surface-0_0_3.md:1' KANBAN.md` → `0`, and `diff` of the item's text against its pre-write copy shows exactly one replaced sentence.
- [x] **D5 — the clause R3's own write falsified is corrected.** `CardItem` pk 1240 (order 1) no longer says `DjangoSchema` / `DjangoMutationExecutionContext` are absent from the Public exports list; the `#djangoschema` history, card 047's closeout, and the open entry-granularity question survive verbatim; `is_complete` is still `False`. Evidence: `grep -c 'are absent from the Public exports list' KANBAN.md` → `0`, while `grep -c 'has no `DjangoSchema` entry' KANBAN.md` → `1`.
- [x] **D6 — the regenerate is stable and its output is exactly this cycle's.** Three `cmp` exit 0 across two consecutive regenerates, three `--check` exit 0, and the three step-3 baseline diffs reduce to five `docs/GLOSSARY.md` lines, three `KANBAN.md` lines, and the matching `KANBAN.html` data-block change — nothing else. Evidence: the commands and outputs of steps 3, 7, and 9, with a baseline taken **before** any DB edit. Not evidenced by `git diff` being clean, which is impossible for all four paths.
- [x] **D7 — `import_spec_terms` ran in its writing form, then green on `--check`.** Evidence: both commands' output, `--check` printing `OK: 49 done cards have glossary links.` and exiting 0, plus a sentence in the build report stating that the writing form reconciles every done card so its `iterdump()` footprint legitimately exceeds card 6.
- [x] **D8 — the durable-doc audit ran read-only and reported.** `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`, and the root `README.md` were read against the reconciled spec; the 37-entry `__all__`, the literal-tuple export pin in `tests/base/test_init.py`, and the five-marker legend were re-derived rather than trusted. Evidence: the step-10 script printing `len(__all__) 37 | pin matches True` with both set differences empty, the legend's five rows, `9` for `grep -c 'planned by TODO-' docs/TREE.md`, and no `## Current surface` / `## Package architecture` heading in `docs/README.md`. `git status --short docs/README.md docs/TREE.md README.md` shows **no change from this pass**.
- [x] **D9 — the three-direction cross-reference sweep ran and every link resolves.** To spec-006 (per-file **occurrence** counts, not matching lines), from spec-006 (8 definitions, 8 used, 0 undefined, 0 unused, all resolving on disk), and from the rationale at `docs/SPECS/appx/` depth (16 definitions, 16 used, 12 fragments all slugging to real spec-006 headings). Evidence: the step-11 script's output, plus the report naming the spec-007 cycle's files and `docs/review/*` as new inbound sites that were reported and not edited.
- [x] **D10 — the staged-anchor sweep is zero outside the board files.** Evidence: `grep -rEn 'TODO\(spec-006|TODO-(ALPHA|BETA|STABLE)-006' . | grep -v '^./.venv'` output, classified by file, with every hit in `KANBAN*` / `BACKLOG.md` / this cycle's own artifacts.
- [x] **D11 — the archive is verified complete and unchanged.** Spec and terms CSV at their archived paths, `SpecDoc.path` matching, `card.glossary_links.count()` equal to the CSV's row count, both `KANBAN.md` references to the archived spec resolving, and the rationale companion present at `docs/SPECS/appx/`. Evidence: the step-13 block — `DONE-006-0.0.3 done 0.0.3 | glossary_links 7`, `SpecDoc.path docs/SPECS/spec-006-public_surface-0_0_3.md`, `grep -c '' …-terms.csv` → `8` (header + 7 rows), `check_spec_glossary` → `OK: 7 terms …` exit 0, and the CSV absent from `git status --short`.
- [x] **D12 — the concurrent tree was reported, never reverted.** No `git checkout`, `git restore`, `git stash`, or `git worktree` was run; no baseline-dirty file outside this item's writable set was edited; any fifth growth event is recorded for Worker 0 to append to the plan. Evidence: `git status --short` before and after, and `git log --stat -3` over the four written paths proving this cycle's work was not swept into another session's commit.

### Notes for Worker 2 (dispatch constraints)

- **Never hand-edit a generated file.** `docs/GLOSSARY.md`, `KANBAN.md`, and `KANBAN.html` are outputs. Edit the DB through the **Django ORM** with `.save()` / `.objects.create()` — a queryset `.update()` or a raw SQL write skips the `post_save` hook that creates the `UUIDModel` side-row the renderers query, and breaks the render. Then regenerate.
- **Never `git checkout`, `git restore`, `git stash`, or `git worktree` anything**, for any reason, including "tidying" churn. Three other sessions are writing this tree.
- **Never revert concurrent churn**, and never treat a same-size binary diff as a no-op. Compare `iterdump()`.
- **Stop and report rather than tidy.** Unexpected churn in a file this plan does not name is a stop-and-report in the build report (`ARTIFACT.md` `### Validation run`), never a revert.
- **Writable set for this pass, exhaustively:** `examples/fakeshop/db.sqlite3` (via the ORM only), `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html` (via the renderers only), this artifact, and `docs/builder/worker-memory/spec-006-worker-2.md`. Nothing else — no source, no tests, no spec, no rationale, no `docs/README.md`, no `docs/TREE.md`, no root `README.md`, no terms CSV, no `docs/review/`, none of the spec-007 cycle's files, and not the build plan (Worker 0 owns it).
- **Do not read** `docs/builder/worker-memory/spec-006-worker-1.md`, `-worker-0.md`, `-worker-3.md`, the un-namespaced `worker-*.md` files, or the `spec-005-*` namespaced ones. Do not read either rationale file (`BUILD.md`: Worker 2 never reads it — that is the point of the move).
- **Run `ruff` scoped, or not at all.** This pass touches no `.py` file, so `uv run ruff format` / `check` have nothing of this pass's to run on; **never** run either against `.` (it would rewrite the concurrent session's four dirty source and test files). Record that reasoning in `### Validation run` rather than a pass/fail for a command with no target.
- **Never commit, never branch.** Hand the mixed diff to the maintainer.
- Keep the `### Failability proofs`, `### Hot-path budget`, and `### Floor verification` headings and write the not-applicable literals from `### Declarations`.

### Notes for Worker 1 (spec reconciliation)

For my own final-verification pass. **No spec edit is made now**, per the dispatch.

1. **No spec edit appears to be owed by R3, and one candidate was examined and rejected.** After step 4, every one of the 37 `__all__` names carries a root-re-export bullet that links at least one per-feature entry with a `shipped` marker, so condition 3 at `spec:44` becomes satisfiable for the whole roster for the first time — which is the spec being *satisfied*, not amended. `spec:17`'s bullet-vs-group distinction and `spec:76`'s two licensed placements are untouched by construction (no group was added, moved, or demoted).
2. **The honest residue to state at final verification rather than paper over.** Two of the five bullets (`DjangoSchema`, `DjangoMutationExecutionContext`) satisfy condition 3 in its **letter** — their glosses link per-feature entries carrying `shipped` markers — while neither name has an entry *of its own*. That granularity question is card 052's by `### Maintainer decision 2`, it is already recorded on `CardItem` pk 1240, and step 5's rewrite of that row deliberately keeps it open. Do not let the final-verification summary read as though the entry question were closed.
3. **`__version__` resolved to R2's first branch, so nothing was added to card 052 for it.** If a later reader expects a card-052 residue there, the reason there is none is that `#joint-version-cut` was a defensible existing anchor: its entry names `__version__` as one of the five version-quintet members. Worth confirming at final verification that the anchor and its marker are still there.
4. **The pk-1240 edit is a one-`CardItem` widening of the dispatch's deliverable 2.** Audit it explicitly rather than as part of D3/D4: confirm the widening is the narrow single-sentence surgery this plan specifies, that the rest of the item is byte-identical, and that Worker 3 recorded a position on the scope call. If Worker 3 rejects the widening, the row's text reverts and the falsified clause becomes a card-052 sweep item — record which outcome landed.
5. **Card 052's five-site sweep.** `bld-003-final.md` item 7 records `KANBAN.md:314` as a fifth card-052-adjacent site the plan's retirement table omits; R3 has now written it for a different reason (step 5's third row). At final verification, note for the card-052 closeout that the sweep is five sites and that one of them has already moved.
6. **Sites reported and not edited, to re-check at final verification:** `docs/SPECS/appx/spec-007-…-rationale.md` and the `bld-007-*` artifacts now reference spec-006 (new since the plan's inbound table); the five deleted committed `docs/review/rev-*.md` remain escalated to the maintainer; the transport session's four source/test files remain baseline-dirty. None is this cycle's to touch, and `## The single-ownership law` clause 3's licence is spent.

---

## Build report (Worker 2)

Executed 2026-08-14 at HEAD `947f7494` (`git rev-parse --short HEAD` re-derived at the start and again at the end of the pass — unmoved). Every number below was measured as it was written; every command is quoted with its real output.

### Files touched

Grounded in `git status --short`, run before and after the pass.

- `examples/fakeshop/db.sqlite3` (`M`, baseline-dirty from the concurrent card-wrap) — written **only** through the Django ORM with `.save()`, per step 4 and step 5: `BoardDoc` pk 41 `body` (7,843 -> 8,932 bytes), `CardItem` pk 1260 (1,264 -> 1,277 chars), pk 1270 (1,150 -> 1,225), pk 1240 (525 -> 671). Plus the step-6 `import_spec_terms` reconciliation.
- `docs/GLOSSARY.md` (`M`) — **regenerator output only** (`scripts/build_glossary_md.py`). Five bullet lines changed; no hand edit.
- `KANBAN.md` (`M`, baseline-dirty) — **regenerator output only** (`scripts/build_kanban_md.py`). Three bullet lines changed; no hand edit.
- `KANBAN.html` (`M`, baseline-dirty) — **regenerator output only** (`scripts/build_kanban_html.py`). One line changed (the embedded data block, line 97); the hand-edited Vue shell untouched.
- `docs/builder/bld-006-r3-doc_completion_archive.md` (`??`) — this build report appended; the 12 `### Dispatched findings checklist` boxes ticked; `Status:` set to `built`. The `## Plan (Worker 1)` section is byte-unchanged apart from the 12 box markers.
- `docs/builder/worker-memory/spec-006-worker-2.md` (gitignored) — one memory entry appended.

**Nothing else was written.** `docs/README.md`, `docs/TREE.md`, the root `README.md`, every spec, both rationales, the terms CSV, `docs/review/`, all package source and all tests were read only. Proof: `git status --short docs/README.md docs/TREE.md README.md` prints **nothing**, `git status --short docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv` prints **nothing**, and the spec's mtime (`2026-08-14 12:00:04`) predates this pass's first regenerate (`KANBAN.md` at `12:50:04`, `docs/GLOSSARY.md` at `12:50:08`).

### Tests added or updated

**None owed and none added.** No package source changed, so `AGENTS.md` "Add tests in the same change as code" has no code to attach a test to, and this cycle's `## Build-wide context flags` make every source and test file read-only. The verification commands standing in for a test run, each with its real result:

- `uv run python scripts/build_kanban_md.py --check` -> `KANBAN.md is up to date.` exit 0.
- `uv run python scripts/build_kanban_html.py --check` -> `KANBAN.html is up to date.` exit 0.
- `uv run python scripts/build_glossary_md.py --check` -> `docs/GLOSSARY.md is up to date.` exit 0.
- `cmp` across two consecutive regenerates: all three exit 0 (see `### Validation run`).
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have glossary links.` exit 0.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md` -> `OK: 7 terms - all have glossary entries and at least one spec link.` exit 0.
- `uv run python scripts/check_trailing_commas.py --check KANBAN.md docs/GLOSSARY.md` -> exit 0 (`--check` only; its default auto-fix mode is a hand edit of a generated file by another name).
- The step-8 roster script -> `__all__ 37 | root bullets 38`, `missing bullets: []`, `bullets not in __all__: ['SerializerMutation']`, `total bullets in section: 48`, `unlinked bullets in the whole section: []`.

**No `pytest` was run, in any form, with or without `--cov*` flags.** Nothing in this pass's diff is executed by the suite.

### Validation run

**`uv run ruff format` and `uv run ruff check --fix` are NOT APPLICABLE and were not run.** This pass changed no `.py` file, so both commands have no target of this pass's; a repo-wide `.` run would have rewritten the concurrent transport session's four dirty source and test files, and that churn is not this pass's to create or to revert. Recorded as reasoning rather than as a pass/fail for a command with no target, per the plan's `### Notes for Worker 2 (dispatch constraints)`.

**Step 1 — starting state.** `git rev-parse --short HEAD` -> `947f7494`. `git status --short`:

```text
 M KANBAN.html
 M KANBAN.md
 M django_strawberry_framework/_boundary_ordering.py
 M django_strawberry_framework/middleware/request_body.py
 M docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
 M docs/SPECS/spec-002-optimizer-0_0_2.md
 M docs/SPECS/spec-006-public_surface-0_0_3.md
 M docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
 D docs/review/rev-_cross_web_patches.md
 D docs/review/rev-_django_patches.md
 D docs/review/rev-_strawberry_patches.md
 D docs/review/rev-apps.md
 D docs/review/rev-conf.md
 M examples/fakeshop/db.sqlite3
 M examples/fakeshop/test_query/test_transport_api.py
 M tests/test_views.py
?? docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md
?? docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
?? docs/builder/bld-006-r1-rationale_move.md
?? docs/builder/bld-006-r2-spec_reconciliation.md
?? docs/builder/bld-006-r3-doc_completion_archive.md
?? docs/builder/bld-007-r1-rationale_move.md
?? docs/builder/bld-007-r2-spec_reconciliation.md
?? docs/builder/build-006-public_surface-0_0_3.md
?? docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md
?? docs/review/rev-_boundary_ordering.md
?? docs/review/review-0_0_14.md
```

Every entry is accounted for by the plan's `## Baseline-dirty out-of-scope files` plus its three recorded growth events, **with one correction and one fourth growth event, both reported and neither reverted:**

- **CORRECTION to the dispatch's premise, and it matters for verification.** `docs/GLOSSARY.md` was **NOT** baseline-dirty — it is absent from step 1's `git status --short`. So for that one path `git diff` **is** available as an independent verification, and it was taken (below). The other three written paths (`KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`) were baseline-dirty exactly as the plan says, and for those the baseline instruments are the only verification.
- **Fourth growth event (new since step 1, appeared mid-pass): `docs/builder/bld-007-r3-doc_completion_archive.md` (`??`)** — the concurrent spec-007 residual cycle reaching its own R3. Not touched, not read, not reverted. Worker 0 to append to the plan's growth list.

**Step 2 — DB semantic baseline** (`iterdump()`, read-only URI open, never file bytes):

```shell
uv run python - <<'PY' > /tmp/dsf-r3-baseline/db-before.sql
import sqlite3
conn = sqlite3.connect("file:examples/fakeshop/db.sqlite3?mode=ro", uri=True)
for line in conn.iterdump():
    print(line)
PY
wc -l /tmp/dsf-r3-baseline/db-before.sql   # -> 11220
```

**Step 3 — regenerate-to-temp baselines, taken BEFORE any DB edit.** All three renders succeeded (`Wrote 69 cards (excluded 1 backlog cards) and 15 board docs`; `Wrote 70 cards, 15 board docs, and 11 lookup arrays`; `Wrote 142 terms, 146 category memberships, 1042 spec mentions across 49 specs`), and **all three diffs against the working-tree files were EMPTY:**

```text
diff /tmp/dsf-r3-baseline/KANBAN.md   KANBAN.md        -> (empty)
diff /tmp/dsf-r3-baseline/KANBAN.html KANBAN.html      -> (empty)
diff /tmp/dsf-r3-baseline/GLOSSARY.md docs/GLOSSARY.md -> (empty)
```

This is the single most useful measurement of the pass and it is better news than the plan anticipated: **the concurrent card-wrap's pending state was already fully rendered into the three working-tree files.** The card-wrap had written the DB *and* regenerated. So the subtrahend for step 9 is zero, and every line the step-9 baseline diffs show is unambiguously this cycle's own output — no attribution judgement needed anywhere.

**Step 7 — two-consecutive-regenerate byte-stability.** Both rounds of all three renderers ran; then:

```text
cmp KANBAN.md        /tmp/dsf-r3-baseline/KANBAN.md.pass1        -> exit 0
cmp KANBAN.html      /tmp/dsf-r3-baseline/KANBAN.html.pass1      -> exit 0
cmp docs/GLOSSARY.md /tmp/dsf-r3-baseline/GLOSSARY.md.pass1      -> exit 0
```

plus the three independent `--check` confirmations quoted in `### Tests added or updated`.

**Step 9 — `git status --short` after the work.** Identical to step 1's listing except for the four intended `M` paths (`docs/GLOSSARY.md` newly `M`; `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3` already `M`) and the fourth growth event named above. **No unexpected churn, so no stop-and-report was owed and no tidy-up was performed.** No `git checkout`, `git restore`, `git stash`, or `git worktree` was run at any point in this pass, for any reason.

**Step 9 — the baseline diffs, which are the acceptance criterion.**

`diff /tmp/dsf-r3-baseline/GLOSSARY.md docs/GLOSSARY.md` -> exactly **five** lines: `26a27,28` (the two `DEFAULT_*` bullets), `38a41` (`DjangoMutationExecutionContext`), `44a48` (`DjangoSchema`), `59c63` (`__version__` gaining its link and clause). Nothing else.

**Independent confirmation, available because `docs/GLOSSARY.md` was clean at baseline:** `git diff --stat -- docs/GLOSSARY.md` -> `1 file changed, 5 insertions(+), 1 deletion(-)`, and `git diff -U0` shows the identical four hunks at `@@ -26,0 +27,2 @@`, `@@ -38,0 +41 @@`, `@@ -44,0 +48 @@`, `@@ -59 +63 @@`.

`diff /tmp/dsf-r3-baseline/KANBAN.md KANBAN.md` -> exactly **three** changed lines: `314c314` (pk 1240), `319c319` (pk 1260), `322c322` (pk 1270) — the three line numbers the plan predicted. Nothing else.

`diff /tmp/dsf-r3-baseline/KANBAN.html KANBAN.html` -> exactly **one** changed line: `97c97`, the embedded data block. Measured content of that change: length 1,934,444 -> 1,934,674 (delta **+230** bytes), with `carries no status-shaped section`, `is spent`, and `closed the roster half` each going 0 -> 1 occurrence. Measured and worth recording: `DEFAULT_ERROR_POLICY` occurs **0** times in that line both before and after — the `namespace='glossary'` `BoardDoc` is not embedded in `KANBAN.html`, so the HTML change is exactly the three card-052 bullets and nothing glossary-side.

**Step 9 — the `iterdump()` comparison.** 11,220 -> 11,224 lines. Classified by table with a `difflib.SequenceMatcher` opcode walk (not a line grep):

| Table | Rows in the diff | Attribution |
|---|---|---|
| `kanban_boarddoc` | 1 (pk 41) + 5 embedded body lines | **this pass**, step 4 |
| `kanban_carditem` | 3 (pks 1240 / 1260 / 1270) | **this pass**, step 5 |
| `glossary_glossaryspecmention` | 1042 | **this pass**, step 6's `import_spec_terms` |
| `kanban_cardglossaryterm` | 1042 | **this pass**, step 6's `import_spec_terms` |

`tables with row-count change: {}` — **no table gained or lost a row**, and **no concurrent writer's row appears in the diff at all**, which follows from step 3's empty baselines. The 2,084 reconciled rows were then measured a second way, to say precisely what `import_spec_terms` did to them: with every `'YYYY-MM-DD HH:MM:SS.ffffff'` literal normalised, **both tables are byte-identical before and after** (`identical ignoring timestamps: True`, 0 rows differing in each direction). So the writing form's wide footprint is a `modified`-timestamp touch on every row of both tables, with pks and content preserved — a legitimately wider diff than card 6 alone, exactly as the plan warned, and **not a defect**.

**Step 9 — proof this cycle's work was not swept into another session's commit,** with `git log --stat`, never `git status`: `git rev-parse --short HEAD` -> `947f7494` (unmoved), and `git log --stat -3 -- docs/GLOSSARY.md KANBAN.md KANBAN.html examples/fakeshop/db.sqlite3` returns `947f7494` ("retarget cards 050 and 051 onto 0.0.15", 2026-08-10) as the most recent commit touching any of the four — which predates this cycle. All four writes are still uncommitted and attributable.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Packaging of the ORM edits: three heredoc scripts, not one or four** (a plan-declared discretion item). One for `BoardDoc` 41, one for the three `CardItem` rows, and one read-back verifier in between. The split is what let the five bullet texts be verified from the DB *before* the `CardItem` write landed, so a bullet-text defect could not have been compounded by a second write on top of it. All assertions and every `.save()` are exactly as the plan fixed them.
- **The five bullet texts were verified by measurement, not by trusting the string concatenation** — the plan required this explicitly. Re-read `BoardDoc.objects.get(pk=41).body`, split to lines, and asserted `lines.count(exact_text) == 1` for each. Their measured character counts are **158 / 170 / 313 / 357 / 128**, matching the plan's five predicted counts exactly, in the plan's order.
- **The four insertion positions were verified by rendered ordinal, not by assuming the anchor put them right.** Root-group line indices after the write: `BigInt` 2, `DEFAULT_ERROR_POLICY` 3, `DEFAULT_RESOURCE_POLICY` 4, `DjangoConnection` 5; `DjangoMutation` 16, `DjangoMutationExecutionContext` 17, `DjangoMutationField` 18; `DjangoResourcePolicyExtension` 23, `DjangoSchema` 24, `ErrorPolicy` 25; `auto` 38, `__version__` 39. Every position is the one the plan's step-4 table prescribes, and the case-folded sort plus its three standing exceptions are intact.
- **The six anchors the five bullets point at were re-verified for existence AND marker**, since `spec:44` condition 3 reads the stamp rather than the bare word — via a markup-rendering slugger over `docs/GLOSSARY.md`'s headings: `#errorpolicy` `shipped (0.0.14)`, `#resourcepolicy` `shipped (0.0.14)`, `#production-error-policy` `shipped (0.0.14)`, `#execution-resource-policy` `shipped (0.0.14)`, `#djangomutation` `shipped (0.0.11)`, `#joint-version-cut` `shipped (0.0.13)`. The `#joint-version-cut` entry was additionally confirmed to **name `__version__`** in its body, which is the whole basis for R2's first-branch resolution.
- **Row 8's replacement text asserts four facts about other files; all four were re-derived mechanically before the write, not read from R2's report.** `grep -oiE 'visibility[ -]status'` -> **0** occurrences in `docs/SPECS/spec-002-optimizer-0_0_2.md` and **0** in `docs/SPECS/spec-006-public_surface-0_0_3.md`; `grep -c 'spec-002-visibility'` in the spec-002 rationale -> **0**; the discharge record exists at `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:503` as `## The discharged deferral — Visibility status retired by the spec-006 cycle`; the sentence at `:261` now reads `[Shipped slices][spec-002-shipped], which absorbed …`; and spec-002's surviving `##` headings are `Purpose` / `Problem statement` / `Architecture decision` / `Shipped slices` / `Coordination with …` / `References` / `Implementation checklist` — **no status-shaped section**.
- **The two surgical rewrites were proved surgical by a sentence-level set difference against a pre-write snapshot** (`/tmp/dsf-r3-baseline/carditems-before.txt`), not by eye. pk 1270: 4 sentences before and after, **first 3 byte-identical**, exactly one sentence removed and exactly one added. pk 1240: the first sentence replaced by two, the trailing Card-047-closeout sentence surviving verbatim (it appears in neither the removed nor the added set).
- **`is_complete` is `False` on all three `CardItem` rows** and was asserted so immediately before each `.save()`. No card was moved, no status flipped, no `SpecDoc` repointed, no CSV edited.
- **Scratch root is `/tmp/dsf-r3-baseline/` — outside the repository**, which was not discretionary. `docs/shadow/` was deliberately not written; it is not in this pass's authorized writable set.

### Notes for Worker 3

**The baselines you need to re-derive every claim, and where they live.** All five were taken **before** any DB edit and none can be reconstructed after the fact:

- `/tmp/dsf-r3-baseline/db-before.sql` — the pre-write `iterdump()` (11,220 lines). `db-after.sql` (11,224) sits beside it.
- `/tmp/dsf-r3-baseline/KANBAN.md`, `KANBAN.html`, `GLOSSARY.md` — the pre-write regenerate-to-temp baselines. **All three diffed empty against the working tree**, which is the fact that makes attribution trivial for this pass; re-take them at your own timestamp if you want to confirm the concurrent writer has still not moved.
- `/tmp/dsf-r3-baseline/*.pass1` — the first-regenerate copies the byte-stability `cmp`s compare against. To re-derive the stability claim: regenerate all three again and `cmp` against these, or simply run the three `--check` forms, which is the cheaper independent instrument.
- `/tmp/dsf-r3-baseline/carditems-before.txt` / `carditems-after.txt` — the pre- and post-write `CardItem` texts, which is what makes "exactly one sentence replaced" auditable for pk 1270 and pk 1240 rather than asserted.

**Two things to weigh, both flagged rather than decided:**

1. **The `DjangoSchema` bullet is 357 characters, 20 past the section's previous longest.** The plan measured this, named it as the one length worth weighing, and accepted it. It is the only one of the five covering a class with no glossary entry of its own, so its gloss carries the two anchors that do document what it does. I implemented it as written; the length call is the plan's, and it is the single most reasonable thing in this diff to push back on.
2. **The two unlinked bullet names (`DjangoSchema`, `DjangoMutationExecutionContext`) satisfy `spec:44` condition 3 in its letter, not in the shape a reader might expect.** Their glosses link `shipped`-marked per-feature entries; neither name has an entry of its own. That granularity question is card 052's by `### Maintainer decision 2` and stays open on `CardItem` pk 1240 by construction. Read pk 1240's new text before judging: it deliberately narrows the open question rather than closing it.

**One measurement to re-take rather than trust, and it is not from this pass:** the plan's step-10 expectation of `experimental` / `aspirational` at **0 occurrences across all five durable docs** is wrong for `KANBAN.md`. See `### Notes for Worker 1 (spec reconciliation)` item 3 — both hits are prose, neither is a status marker, and no correction is owed, but a reviewer re-running the plan's numbers will hit the discrepancy and should not read it as a defect this pass introduced.

**No shadow file was generated or read in this pass, and `scripts/review_inspect.py` was not run** — the pass touches no `.py` file, so `BUILD.md` `### When to run the helper during build` does not reach it.

### Notes for Worker 1 (spec reconciliation)

Written on disk here, per `worker-2.md` `### Spec amendments go on disk, not in the return message`. **No spec, rationale, or terms CSV was edited by this pass.** None of the items below is a spec amendment; R3 found no spec claim needing one, which agrees with the plan's own item 1.

1. **The plan's D2 evidence formula is unsatisfiable at this tree, and the substitute is recorded.** D2 says its evidence is that "`git diff -- docs/SPECS/spec-006-public_surface-0_0_3.md` is empty". It is not, and cannot be: **R2 of this same cycle legitimately rewrote that spec and the rewrite is uncommitted** — `git diff --stat` reports `52 insertions(+), 62 deletions(-)`. What D2 actually needs to claim is that *R3* made no spec edit, and the evidence taken for that is the spec's mtime `2026-08-14 12:00:04`, which predates this pass's earliest write (`KANBAN.md` at `12:50:04`). I ticked D2 on that substitute evidence and am naming the swap rather than letting a later pass read the box as though the literal command had been run and come back empty. **Recommended replacement**, in `### Dispatched findings checklist` box **D2**, for the wording `and \`git diff -- docs/SPECS/spec-006-public_surface-0_0_3.md\` is empty`: `and the spec is byte-unchanged by R3 — its mtime predates R3's first regenerate (R2's own uncommitted rewrite of the same file means \`git diff\` cannot be empty for it, and never could be during this cycle)`.
2. **The row-8 text quotes the spec-002 rationale's discharge heading with an ASCII hyphen where the heading on disk carries an em dash.** The plan fixed this text and explicitly instructed keeping the item's ` - ` house style, so I wrote it as specified. The consequence is narrow but real: the new `CardItem` pk 1260 text renders `` `## The discharged deferral - Visibility status retired by the spec-006 cycle` `` while `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:503` reads `## The discharged deferral — Visibility status retired by the spec-006 cycle`. A reader searching the rationale for the quoted string will not find it. **Recommended replacement**, in the plan's `#### Step 5 — Discharge the card-052 prose` row-8 fenced replacement text, for `` `## The discharged deferral - Visibility status retired by the spec-006 cycle` ``: `` `## The discharged deferral` `` — naming the heading's distinctive stem sidesteps the dash question entirely, keeps the item's ASCII house style, and stays greppable. Not applied: the five bullet texts and three prose blocks are declared non-discretionary, so changing one is Worker 1's call, not mine.
3. **A plan measurement that does not hold, reported because a later pass will re-run it.** Plan step 10 records the three retired markers' occurrence counts as `experimental` 0/0/0/0/0 and `aspirational` 0/0/0/0/0 across the five durable docs. Re-measured this pass with `grep -oi <token> | wc -l` (occurrences, not matching lines): `docs/README.md` 0/0, `docs/TREE.md` 0/0, `docs/GLOSSARY.md` 0/0, root `README.md` 0/0 — but **`KANBAN.md` carries 1 of each**. Both were read and **neither is a status marker on a consumer-visible entry**, so no correction is owed and none was made: `KANBAN.md:80` says "the product-catalog Layer 3 aspirational schema block remains commented until those subsystems ship" (describing a commented-out example schema block), and `:1376` is a card checklist item reading "no `# experimental` markers in shipped code" — which *names* the marker as a thing to sweep for. The plan's D9 counts were taken across `docs/README.md` / `docs/TREE.md` / `docs/GLOSSARY.md` / `TODAY.md`, so the discrepancy is a scope difference between D9's four docs and step 10's five, not a regression. **Recommended replacement**, in `#### Step 10 — The durable-doc audit`, for `\`experimental\` 0/0/0/0/0, \`aspirational\` 0/0/0/0/0`: `\`experimental\` 0/0/0/0 across \`docs/README.md\` / \`docs/TREE.md\` / \`docs/GLOSSARY.md\` / root \`README.md\` plus **1** in \`KANBAN.md\`, \`aspirational\` the same shape — both \`KANBAN.md\` hits are prose (a commented-out example schema block at \`:80\`, and a card checklist item at \`:1376\` naming \`# experimental\` as a thing to sweep for), not markers, and require no correction`.
4. **`order` values and rendered ordinal positions are not the same thing, and the plan's step-8 spot-check conflates them.** It asks that the three rewritten bullets render "in their original order positions (1, 8, 11)". 1 / 8 / 11 are the `CardItem.order` column values; the rendered ordinals inside `#### Scope` are the **1st, 6th and 9th** bullets, because the `order` sequence is sparse. Both are correct and nothing moved — this pass changed `text` only and touched no `order` — but the check as literally worded fails against a correct render. **Recommended replacement**, in `#### Step 8 — Spot-check the rendered result`, for `in their original order positions (1, 8, 11)`: `at their unchanged \`CardItem.order\` values 1 / 8 / 11, which render as the 1st, 6th and 9th bullets of \`#### Scope\` because the order sequence is sparse`.
5. **Two audit findings for the maintainer or card 052, neither fixed here.** (a) `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` is now the **largest inbound referencer of spec-006** at 53 occurrences, which is expected for a companion but is worth a glance at final verification for restatement of contract text the spec owns — I did not read it (Worker 2 never reads a rationale), so this is a count observation, not a content finding. (b) The five deleted committed `docs/review/rev-*.md` remain deleted and unrestored, and `docs/builder/bld-007-r3-doc_completion_archive.md` is a **fourth growth event** appearing mid-pass. Both stay escalated; nothing in `docs/review/` was touched.
6. **Everything the plan predicted for the read-only half held exactly.** `len(__all__) 37 | pin matches True` with both set differences empty; the legend carries exactly the five markers `shipped` / `planned for X.Y.Z` / `deferred` / `alpha constraint` / `post-1.0.0` and still renders **before** `## Public exports` (lines 12 and 22); `grep -c 'planned by TODO-' docs/TREE.md` -> **9**; `docs/TREE.md` references spec-006 **0** times; `docs/README.md` carries **no** `## Current surface` and **no** `## Package architecture` heading; the one `in flight` hit in `docs/GLOSSARY.md` (`:285`, "a type already in flight") is prose, per D9; spec-006 has **8** definitions, 8 used, 0 undefined, 0 unused, all resolving; the rationale has **16** / 16 / 0 / 0, all resolving, and its **12** fragment-bearing definitions all slug to real spec-006 headings under a markup-rendering slugger (`#decision-for-003` included, since a dotted version slugs to `003`); the staged-anchor sweep finds **3** hits in **2** files, both this cycle's own artifacts quoting the pattern (`build-006-…:31` and `:307` as `TODO(spec-006`, `bld-006-r3-…:426` as `TODO-ALPHA-006`) and **zero** in source, tests, or any standing doc; and the archive is complete and unchanged — `DONE-006-0.0.3 done 0.0.3 | glossary_links 7`, `SpecDoc.path docs/SPECS/spec-006-public_surface-0_0_3.md`, terms CSV **8** lines (header + 7 anchor rows) and absent from `git status`, all three archived files present.

**One count the plan asked for a measurement of rather than a target**, taken and reported as instructed: `grep -c 'spec-006' KANBAN.md` -> **5** matching lines (141, 314, 319, 322, 4824), carrying **13** occurrences of the token. The pre-write figure was 7 occurrences by the plan's own inbound table; both the 5-line and 13-occurrence readings are quoted so no later pass has to guess which was measured. Lines 141 and 4824 are the two generated references to the archived spec and both still read `docs/SPECS/spec-006-public_surface-0_0_3.md`; 314 / 319 / 322 are the three rewritten card-052 bullets.

#### Addendum to `### Validation run` — a FIFTH growth event, recorded at the close of this pass

`git status --short`, re-run after the build report and memory entry were written, shows one path that was absent from **both** step 1's listing and step 9's: **`django_strawberry_framework/_cross_web_patches.py` (`M`)**. HEAD is still `947f7494`. It is the concurrent transport / boundary-ordering session extending its working set to a fifth file (its other four — `_boundary_ordering.py`, `middleware/request_body.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py` — are the plan's third growth event, and `docs/review/rev-_cross_web_patches.md` is one of the five deleted committed review artifacts, which is consistent with that session working this module).

**Reported, not reverted, not read, not touched** (`AGENTS.md` rule 34; this cycle is source-read-only). Worker 0 to append it to the plan's growth list alongside the fourth event (`docs/builder/bld-007-r3-doc_completion_archive.md`). It changes nothing about this pass's diff: the four paths R3 wrote are unaffected, and the three `--check` forms were re-run afterwards and all three still print `is up to date.`

**This is also the practical vindication of the plan's baseline-exception clause.** With two growth events landing inside a single ~50-minute pass, the final gate's repo-wide `pytest` / `ruff` / `git diff --check` will see churn in files this cycle never wrote; a failure attributable to them is reported, never fixed here, and never blocks `final-accepted`.

---

## Review (Worker 3)

Reviewed 2026-08-14 at HEAD `947f7494` (`git rev-parse --short HEAD` re-derived — unmoved from both the plan's and the build report's readings). Every number below was measured in this pass; where it disagrees with a number in the build report or the plan, both are quoted.

**What this pass did to the tree.** It ran the three renderers twice (the prescribed byte-stability instrument) and wrote three temp copies under `docs/builder/temp-tests/r3/`. Nothing else. No DB write, no hand edit, no `git checkout` / `restore` / `stash` / `worktree`, no commit, no branch. `git diff --numstat` over the three generated docs was `1 1 KANBAN.html / 4 4 KANBAN.md / 5 1 docs/GLOSSARY.md` before my regenerates and byte-for-byte the same after, so the review left the reviewed diff untouched.

### High:

None.

### Medium:

None blocking. One Medium-class item is **accepted and escalated** rather than held, under `worker-3.md` `### Acceptance gate`'s escalation clause, because its resolution is a spec edit R3 has no licence to make and Worker 1's final verification owns it. See `### Notes for Worker 1 (spec reconciliation)` item **E1**.

### Low:

#### L1 — pk 1260 quotes a heading that does not exist on disk (ASCII hyphen vs em dash)

`CardItem` pk 1260's new text — rendered at `KANBAN.md:319` — cites the discharge record as `` `## The discharged deferral - Visibility status retired by the spec-006 cycle` ``. Measured: that exact string occurs **0** times in `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`; the heading on disk at `:503` reads `## The discharged deferral — Visibility status retired by the spec-006 cycle` (em dash). A reader who greps the quoted citation from the board finds nothing, which is the one thing a quoted citation exists to prevent.

Why it is Low and not Medium: the distinctive stem (`The discharged deferral`) is still greppable and unique, and the wrong character is the item's own house-style dash, so the failure degrades a citation rather than falsifying a claim. Why it is not Worker 2's defect: the plan fixes this text as **non-discretionary** and explicitly instructs keeping the ` - ` house style, and Worker 2 reported the mismatch with a recommended replacement (`### Notes for Worker 1` item 2) instead of silently editing declared-fixed text. That is the correct disposition of a plan defect found at build time. **Recommended change** — Worker 1's, at final verification: adopt Worker 2's own proposal and shorten the citation to `` `## The discharged deferral` ``, which sidesteps the dash question, keeps ASCII, and stays greppable. No test expectation; no behavior is affected.

#### L2 — the `DjangoSchema` bullet is a third site for a fact its two linked entries already carry

See `### DRY findings`. Recorded as Low rather than Medium because the duplication is the *cost of the pointer* while the name has no entry of its own, and the structural fix is already card 052's.

### DRY findings

- **`docs/GLOSSARY.md:48` restates both linked entries' construction-time claim.** The bullet says `DjangoSchema` "resolves the [production error policy](#production-error-policy) and the [execution resource policy](#execution-resource-policy) once at construction, installs their extensions". Both linked entries already state exactly that about `DjangoSchema` in their own words — `## Production error policy` (`docs/GLOSSARY.md:1524`): "the package's `DjangoSchema` resolves an `ErrorPolicy` once at construction and installs `DjangoErrorPolicyExtension` to enforce it"; `## Execution resource policy` (`:833`): "`DjangoSchema` resolves it ONCE at construction". `django_strawberry_framework/schema.py::DjangoSchema` says it a third time in its docstring ("**The execution resource policy is resolved here, once.**" / "**The production error policy is resolved here too, and by the same rule.**"). So the bullet is a fourth statement of a fact that had three sites, and a change to the construction-time contract now needs four edits.
  - **Judged, not merely flagged:** this is the live DRY question the plan named for me (`### DRY analysis`, "Duplication risk avoided"), and the answer is *the plan mostly held the line and slipped once*. Four of the five bullets state one distinguishing fact and delegate; this one states three. The reason it slipped is structural, not careless — a gloss for a name with **no entry of its own** has to justify why two foreign anchors are the right destination, and naming what those entries say about the name is the cheapest justification available.
  - **Recommended shape, and it is not an edit to make now.** The right fix is the `DjangoSchema` glossary entry that `### Maintainer decision 2`'s WIDENED block assigns to **card 052**; at that point the bullet collapses to `- [`DjangoSchema`](#djangoschema) — the required schema class for any schema exposing generated mutations.` and the duplication disappears rather than being trimmed. Trimming it now would leave the name with a gloss that documents nothing and two anchors with no stated relevance — strictly worse. **Do not "fix" this before the entry exists**; recorded here so a later pass reads it as weighed rather than missed.
- **Length, re-measured and accepted.** The five bullets are **158 / 170 / 313 / 357 / 128** characters, matching the plan's and the build report's figures exactly, in the plan's order. Against the root group's previous longest (`SerializerMutation`, 267) and the section's previous longest (the `global_id_for` / `decode_global_id` bullet, 337), bullets 3 and 4 are the two outliers. Judged against the convention (`spec:17`: a bullet documents a name; the entry behind the anchor owns the contract): **neither crosses into a second contract.** Re-derived from the five texts themselves — none states a precedence order, a default value, a numeric bound, a validation rule, an error message, or an opt-out spelling, all of which the linked entries do carry (`## Execution resource policy` carries three families of bound and the narrowing rule; `## Production error policy` carries the `DEBUG` pass-through and the `error_policy={"enabled": False}` opt-out). The two long bullets are long because they are the **only** documentation those two names have, which is a granularity problem to close by authoring entries, not a contract problem to close by cutting words. Accepted as written, with L2 above recording the one residue.
- **The existence challenge does not fire.** No new script, helper, constant, registry, indirection, or abstraction is introduced by this pass; the four reusable pieces it needed (`scripts/_kanban_lib.py::configure_django` plus the three renderers) already existed and were reused unmodified. `worker-3.md` `### The existence challenge` says to raise it on grounds, not on a schedule; there are none here.
- **No cross-cohort duplication check is owed.** `## Build-wide context flags` and the plan's `### Declarations` both declare ownership partition none / sequential residual items, and R3 is the only item in flight, so there is no second cohort to compare against.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are unchanged by this pass, which is what `## Build-wide context flags` requires ("this cycle **reconciles the spec to `__all__`, never `__all__` to the spec**"). Independently re-derived rather than accepted: `len(__all__)` is **37**, and the literal-tuple pin in `tests/base/test_init.py::test_public_api_surface_is_pinned` **matches it token for token** (`pin matches True`, `pin-only set()`, `all-only set()`) — a token-level identity check, not a count. `django_strawberry_framework/__init__.py` and `tests/base/test_init.py` both carry mtime `2026-08-06 14:24:50`, eight days before this cycle, so neither was touched. No new public export; none authorized, none made.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. (`## Build-wide context flags`: "`CHANGELOG.md` is closed", `AGENTS.md` rule 21. `git status --short CHANGELOG.md` prints nothing.)

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

**This subsection is the heart of this review**, and it applies in full: the pass's entire diff is three script-rendered docs plus the DB they render from.

**The renderer-and-its-source-in-the-same-pass rule is satisfied, and it is the rule this diff could most plausibly have broken.** The feeding source is a DB, not a docstring, and the check is the same: every line of the three generated files must be reproducible by re-running its renderer from the DB. Re-derived independently:

- I re-ran all three renderers against the current DB and `cmp`'d the outputs against copies of the working-tree files taken **before** my first regenerate (`docs/builder/temp-tests/r3/{KANBAN.md,KANBAN.html,GLOSSARY.md}.w3pre`): **all three byte-identical.** That is the direct test for a hand-edit anywhere in any of the three files, and it passes. A hand-edited line would have been silently reverted by my render and shown up as a `cmp` mismatch.
- **Two consecutive regenerates are byte-stable.** Second round `cmp` against the first round's copies: `STABLE KANBAN.md`, `STABLE KANBAN.html`, `STABLE GLOSSARY`. Confirmed independently by all three `--check` forms: `KANBAN.md is up to date.` / `KANBAN.html is up to date.` / `docs/GLOSSARY.md is up to date.`, each exit 0.
- `uv run python scripts/check_trailing_commas.py --check KANBAN.md docs/GLOSSARY.md` → exit 0. Run in `--check` mode only, for the reason the plan gives.

**The diff footprint is exactly what is claimed, and I can say so more strongly than the dispatch expected** — Worker 2's five step-3 baselines survive on disk at `/tmp/dsf-r3-baseline/` with 12:47 mtimes, so the "impossible to repeat" measurement is in fact re-runnable, and I re-ran it:

| Instrument | Claimed | Measured by me |
|---|---|---|
| `diff /tmp/dsf-r3-baseline/GLOSSARY.md docs/GLOSSARY.md` | 5 lines | **5 lines**: `26a27,28`, `38a41`, `44a48`, `59c63` |
| `diff /tmp/dsf-r3-baseline/KANBAN.md KANBAN.md` | 3 lines at `:314`/`:319`/`:322` | **3 lines**: `314c314`, `319c319`, `322c322` |
| `diff /tmp/dsf-r3-baseline/KANBAN.html KANBAN.html` | 1 data-block line | **1 line**: `97c97` |

**And the "baselines came back empty" claim is corroborated by an instrument Worker 2 did not use.** `git diff --numstat -- KANBAN.md` is `4 4`, one line more than the baseline diff's three. That fourth line is `@@ -248 +248 @@` — a line the baseline diff does **not** show, i.e. one that was already both in the DB and rendered into the working tree at 12:47. So the concurrent card-wrap's contribution to `KANBAN.md` is exactly line 248, this cycle's is exactly 314/319/322, and the two sets are disjoint. That is the attribution the whole baseline apparatus exists to produce, arrived at from the other direction. `docs/GLOSSARY.md` needs no such argument: `git diff --stat` is `5 insertions(+), 1 deletion(-)` with hunks at `@@ -26,0 +27,2 @@`, `@@ -38,0 +41 @@`, `@@ -44,0 +48 @@`, `@@ -59 +63 @@` — identical to the baseline diff, because that path was **not** baseline-dirty (Worker 2's CORRECTION to the dispatch's premise, which I confirm: `docs/GLOSSARY.md` is absent from step 1's `git status --short`).

**Nothing beyond the claimed footprint appeared under my regenerates.** No fourth glossary line, no fourth `KANBAN.md` line, no second `KANBAN.html` line, and `git diff --numstat` was identical before and after. So there is no pending concurrent state and no unrecorded edit to distinguish.

Per-bullet checks, all re-derived from the **rendered** file:

- **The roster arithmetic.** My own script over `__all__` and the root group: `__all__ 37 | root bullets 38`, `missing: []`, `not-in-__all__: ['SerializerMutation']`, section bullets **48**, `unlinked: []`. Matches the build report exactly. Zero duplicate bullet names. The root group spans `docs/GLOSSARY.md:26-62`; the section spans `:22-85`.
- **Every new anchor resolves to a real heading**, checked with a markup-rendering slugger over the rendered file rather than by eye: `#errorpolicy` → `## `ErrorPolicy``, `#resourcepolicy` → `## `ResourcePolicy``, `#production-error-policy` → `## Production error policy`, `#execution-resource-policy` → `## Execution resource policy`, `#djangomutation` → `## `DjangoMutation``, `#joint-version-cut` → `## Joint version cut`. **Zero dangling.** `#djangoschema` and `#djangomutationexecutioncontext` are confirmed **absent**, which is why bullets 3 and 4 leave the name unlinked — the correct choice, and the alternative (linking a slug that does not exist) is what card 047's closeout already removed once.
- **Every one of the six carries a `shipped` marker with a version stamp**, which is what `spec:44` condition 3 actually reads: `shipped (`0.0.11`)` / `shipped (`0.0.14`)` ×4 / `shipped (`0.0.13`)`. And `## Joint version cut`'s body **names `__version__`** explicitly in the version quintet — the entire basis for routing `__version__` to that anchor rather than onto card 052. R2's first-branch resolution holds.
- **Character-for-character against the plan.** All five rendered bullet lines are byte-identical to the plan's five fenced `text` blocks (`block in glossary_text` → True for all five; lengths 158/170/313/357/128). The `#` fence question in `ARTIFACT.md` does not arise — no fenced drop-in.
- **Factual claims verified against source, not against the plan's assertion that it verified them.** `django_strawberry_framework/schema.py::DjangoSchema` line 204 subclasses `strawberry.Schema`; its docstring reads "The REQUIRED schema class for any schema exposing generated mutations"; `resolve_resource_policy` / `resolve_error_policy` are both called in `__init__` before `super().__init__`; `kwargs.setdefault("execution_context_class", DjangoMutationExecutionContext)` is the "installs by default" claim; `_with_resource_policy_extension` / `_with_error_policy_extension` are the "installs their extensions" claim. `error_policy.py:102` is `DEFAULT_ERROR_POLICY = ErrorPolicy()` (an all-defaults instance) and `resolve_error_policy` returns it when nothing is configured (`:122`); `resource_policy.py:308` and `:329` are the same shape. `DjangoMutationExecutionContext`'s docstring is "Hold each generated mutation field's transaction open through value completion", and `_marked_mutation_class` restricts it to **top-level** mutation fields — so the bullet's "each top-level generated mutation's transaction" is precise, not approximate.
- **One claim I specifically tried to falsify and could not.** The `DjangoSchema` bullet says the class "runs generated mutations through `DjangoMutationExecutionContext`" unconditionally, while the code uses `setdefault`, which a consumer can override — an apparent over-claim next to the sibling bullet's careful "installs by default". It is not one: the class docstring makes the override itself contractual — "a consumer needing a custom execution context subclasses `DjangoMutationExecutionContext` and passes it explicitly" — so the unconditional form is the true statement of the contract and the sibling's "by default" is the true statement of the mechanism. Both are right; the asymmetry is intentional.

Rendered `KANBAN.md` checks, against the four things the dispatch names:

- **(a) The retirement reads as done, not deferred.** `:319` opens "`docs/SPECS/spec-002-optimizer-0_0_2.md` carries no status-shaped section any more" and states "The last one, `## Visibility status`, was retired by the spec-006 residual cycle as a cross-spec duplicate under the single-ownership law". The four facts that sentence rests on, re-derived by me rather than read from either report: `grep -oiE 'visibility[ -]status'` → **0** occurrences in `docs/SPECS/spec-002-optimizer-0_0_2.md` and **0** in `docs/SPECS/spec-006-public_surface-0_0_3.md`; `grep -c 'spec-002-visibility'` in the spec-002 rationale → **0**; spec-002's surviving `##` headings are exactly `Purpose` / `Problem statement` / `Architecture decision` / `Shipped slices` / `Coordination with `spec-001-django_types-0_0_1.md`` / `References` / `Implementation checklist` — **no status-shaped section**. All four true.
- **(b) The falsified instruction is gone.** `:322` no longer instructs a reader not to sweep spec-006's two citations; the replacement records the instruction as spent. `grep -c 'public_surface-0_0_3.md:1' KANBAN.md` → **0**, so no raw `path:NN` reference to spec-006 survives in this standing doc (`AGENTS.md` rule 27 preserved, and preserved by removal rather than by rewriting a raw ref into another raw ref).
- **(c) pk 1240's surviving question is intact and still card 052's.** The item's tail is byte-identical to its pre-write form: "Card 047's closeout removed the dangling `#djangoschema` links rather than authoring the entry, matching how the `ErrorPolicy` entries already name the class without linking it; deciding whether the entry should exist is still open." The new sentence **narrows** rather than closes — "what remains open is only whether either name earns an entry and anchor of its own" — which is the disposition `### Maintainer decision 2`'s WIDENED block requires. `grep -c 'are absent from the Public exports list' KANBAN.md` → **0**; `grep -c 'has no `DjangoSchema` entry' KANBAN.md` → **1**. A repo-wide sweep for the falsified claim outside `docs/builder/` finds **zero** surviving instances, so this cycle's own write falsifies nothing it left standing.
- **(d) Every clause about other specs survived verbatim, proved by set difference against the pre-write DB, not by eye.** I reconstructed the pre-write `CardItem.text` values from `/tmp/dsf-r3-baseline/db-before.sql` and ran a sentence-level set difference against the live rows: **pk 1270** — 4 sentences before and after, **exactly one removed and one added, 3 surviving byte-identical**, including the whole live spec-003 divergence this card must settle. **pk 1240** — 2 sentences → 3; the first replaced by two, the Card-047-closeout sentence surviving byte-identically (present in neither the removed nor the added set). **pk 1260** — full rewrite as planned, with exactly one sentence surviving verbatim, and it is the closing `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` sentence the plan promised would survive. All three rows' new text is **byte-identical to the plan's fenced replacement blocks** (`text == plan_block` → True for pk 1260; `plan_block in text` and old-block-absent → True for pk 1270 and pk 1240).
- **(e) `is_complete` is ticked on none of the three.** `CardItem` pk 1240 / 1260 / 1270 all read `is_complete False` live, and all three read `is_complete 0` in the pre-write dump — unchanged, not merely false. All three are on `TODO-ALPHA-052-0.1.0`, section `scope`, at unchanged `order` **1 / 8 / 11**. No card moved, no status flipped, no `SpecDoc` repointed.
- **Rendered position.** The three rewritten bullets are the **1st, 6th and 9th** of card 052's 18-bullet `#### Scope` list, at `KANBAN.md:314`/`:319`/`:322`. One bullet each, no stray markdown, no bullet split or merged.

Section-shape checks (`spec:17`, `:44` and `:76` all rest on this shape, so a group added or moved would falsify R2's reconciliation):

- **Four groups, unchanged, in order**: the root roster lead-in at `:24`, `extensions` at `:65`, `testing` at `:69`, `auth` at `:81`, plus the closing `_Note:_` at `:85`. **No group was added, moved, or demoted** — in particular no listing for `views` / `routers` / `middleware.debug_toolbar`, which `### Maintainer decision 2`'s CORRECTION assigns explicitly to card 052 and not to R3.
- `## Status legend` occupies `:12-20` and still renders **before** `## Public exports` at `:22`, and carries exactly the **five** markers `shipped` / `planned for X.Y.Z` / `deferred` / `alpha constraint` / `post-1.0.0`.
- The `SerializerMutation` bullet still says why it sits outside `__all__`.

**Version strings, statuses and card IDs.** No version string moved: no item touches `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, the glossary package-version line, or `uv.lock`. Notably the new `__version__` bullet states **no version number** — it points at `#joint-version-cut` instead, so the next joint cut moves the quintet without also having to move this bullet. That is the right shape and worth naming as a deliberate avoidance of exactly the drift this spec exists to prevent.

**No obsolete "planned" or old-version wording survives in a file this pass deliberately updated.** The three rewritten card items are now past-tense about what this cycle did and present-tense only about what stays open; the five new glossary bullets carry no staging language and no `TODO(`. The staging-docstring half of this check does not reach this pass: the feeding source is DB rows, and no module docstring changed (`git diff --numstat -- '*.py'` lists only the concurrent session's five files).

**Archive verification, re-derived rather than accepted.** All three archived paths present; `Card.objects.get(number=6)` → `DONE-006-0.0.3 done 0.0.3 | glossary_links 7`; `SpecDoc.path` → `docs/SPECS/spec-006-public_surface-0_0_3.md`; `grep -c ''` on the terms CSV → **8** (header + 7 anchor rows, matching `glossary_links` exactly); the CSV is **absent from `git status --short`** and carries mtime `2026-06-04 14:49:54`, so it is byte-unchanged and `import_spec_terms`' rebuild of card 6's links is safe; `check_spec_glossary` → `OK: 7 terms - all have glossary entries and at least one spec link.` exit 0. Both generated `KANBAN.md` references to the archived spec (`:141`, `:4824`) still read the archived path.

**Link sweep, all three directions.** Inbound occurrence counts (occurrences, not matching lines): `KANBAN.md` 13, `KANBAN.html` 12, `appx/spec-002-…-rationale.md` 13, `appx/spec-006-…-rationale.md` 53, `appx/spec-007-…-rationale.md` 6, `appx/spec-005-…-rationale.md` 1, `spec-005:…` 1, `spec-006` itself 4, plus prior and concurrent cycles' builder artifacts and two `docs/review/` files. Outbound: **spec-006 8 defs / 8 used / 0 undefined / 0 unused / 0 unresolved**; **rationale 16 / 16 / 0 / 0 / 0 unresolved**. Nothing dangles in either direction.

**Staged-anchor sweep.** `grep -rEn 'TODO\(spec-006|TODO-(ALPHA|BETA|STABLE)-006' . | grep -v '^./.venv'` → **4 hits in 2 files**, both this cycle's own artifacts quoting the pattern (`build-006-…:31`, `:307`; `bld-006-r3-…:426`, `:700`). **Zero** in source, tests, `KANBAN.md`, `KANBAN.html`, `BACKLOG.md`, or any standing doc. Card 006 is `DONE-006-0.0.3`, so no `TODO-ALPHA-006` form should exist, and none does outside the artifacts.

### What looks solid

- **The baseline apparatus is the best thing in this diff, and it earned its keep twice.** The step-3 regenerate-to-temp baselines were taken before any write, they came back empty, and the *consequence* of that — every diff line being unambiguously this cycle's — held up under three independent re-derivations (the surviving baselines, `git diff` on the one clean path, and the disjointness of `KANBAN.md:248` from `:314`/`:319`/`:322`). A pass that had skipped step 3 could not have made this claim at all, and no later measurement could have recovered it.
- **The build report reads as measurements, not as a narrative of intentions.** Every claim I re-derived came back equal or corrected-in-my-favour. Bullet lengths, positions, insertion ordinals, anchor markers, sentence-level set differences, `iterdump()` classification, the roster arithmetic — all reproduced.
- **Two reported-and-not-fixed calls were the right calls.** Worker 2 found the plan's row-8 text quoting a heading with the wrong dash and the plan's step-8 check conflating `CardItem.order` with rendered ordinals, and in both cases the plan had declared the text or the check non-discretionary. It reported with a concrete recommended replacement instead of editing declared-fixed prose. That is the boundary working as designed rather than a builder deferring work.
- **Verifying the bullet texts from the DB rather than from the string concatenation** was the plan's requirement and the build report's practice, and it is the check that would have caught a concatenation dropping a space across a line continuation — the single most likely silent defect in a write shaped like this one.
- **The insertion positions were verified by rendered ordinal**, not by trusting that a unique-substring anchor put them in the right place. Re-derived: `BigInt` 2 → `DEFAULT_ERROR_POLICY` 3 → `DEFAULT_RESOURCE_POLICY` 4; `DjangoMutation` 16 → `DjangoMutationExecutionContext` 17 → `DjangoMutationField` 18; `DjangoResourcePolicyExtension` 23 → `DjangoSchema` 24 → `ErrorPolicy` 25; `auto` 38 → `__version__` 39. Every one is where the plan's table puts it, and the group's three standing sort exceptions (`DjangoType`'s position, `aapply_cascade_permissions` following `apply_cascade_permissions`, `auto` and `__version__` closing) are intact and were not "fixed".
- **`import_spec_terms` was run in its writing form and its wide footprint was pre-explained rather than post-excused.** `--check` → `OK: 49 done cards have glossary links.` exit 0, re-run by me.
- **The concurrent tree was reported five times and reverted zero times**, including one growth event recorded *after* the build report was already written rather than quietly folded into it.

### Failability proofs

Not applicable, and the plan's reasoning is correct rather than merely asserted: `BUILD.md` `### What needs a proof, and what does not` scopes proofs to new boundaries, guards, gates, and rejection paths in executable code, and this pass's entire diff is four DB rows and three rendered documents. There is no guard to delete, no comparison to invert, no lock to move, and no permissive value to return. The mandatory re-run floor in `worker-3.md` is arithmetic on Worker 2's recorded row counts; with **zero** boundaries meeting the floor, the empty re-run set is legal by the rule's own terms. **Boundaries re-run: none. Boundaries accepted on Worker 2's record: none — there are none to accept.** Recorded explicitly rather than omitted, because an omitted heading reads as a skipped step.

### Hot-path budget

Not applicable; plan declares no hot path, and I confirm the declaration: nothing in this diff runs per request, per resolver, per row, per connection, or per outbound message. The three renderers are build scripts; the ORM writes are one-shot. No before/after number is owed, so none is missing.

### Floor verification

Not applicable; plan declares floor-verification scope none, and I confirm it: no Django / Strawberry / channels integration seam is touched, no source, no tests, no schema construction. `git diff --numstat -- '*.py'` lists only the concurrent transport session's five files.

### Ruff

**Correctly not run, and I did not run it either.** This pass changed no `.py` file — the written set is `examples/fakeshop/db.sqlite3` plus the three generated docs — so `uv run ruff format .` / `ruff check .` have no target of this cycle's, and a repo-wide run would have rewritten the concurrent transport session's five dirty source and test files (`_boundary_ordering.py`, `_cross_web_patches.py`, `middleware/request_body.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py`). Creating that churn is not this cycle's to create and reverting it is not this cycle's to revert (`AGENTS.md` rule 34). Recorded as reasoning, per `### Notes for Worker 2 (dispatch constraints)`.

### Read-only half stayed read-only

Verified positively rather than inferred from an empty `git status`, because three sessions are writing this tree:

- `git status --short docs/README.md docs/TREE.md README.md` → **nothing**. mtimes `2026-08-10 13:36:02` / `2026-08-07 16:02:17` / `2026-08-07 11:57:43`, all days before this cycle.
- Spec and rationale mtimes all predate this pass's first write (`KANBAN.md` at 12:50): spec-006 `12:00:04`, its rationale `12:01:19`, spec-002 `11:23:32`, spec-002's rationale `11:35:40`. Terms CSV `2026-06-04`.
- `docs/review/`'s deletions are untouched by this cycle. **One change since the build report, and it is another session's:** `docs/review/rev-_cross_web_patches.md` now shows `M` where step 1 recorded `D` — that session restored and rewrote the file it also has open as `_cross_web_patches.py`. The other four remain `D`; the two untracked additions remain untracked. **Reported, not reverted, not touched.** See `### Notes for Worker 1` item **N4**.

Spot-checks of Worker 2's read-only audit findings, re-taken rather than accepted: `grep -c 'planned by TODO-' docs/TREE.md` → **9**; `grep -c 'spec-006' docs/TREE.md` → **0**; `docs/README.md` carries **no** `## Current surface` and **no** `## Package architecture` heading; the legend's five markers as listed above; occurrence counts (`grep -oi | wc -l`, occurrences not lines) of `experimental` / `aspirational` / `in flight` across the five durable docs — `docs/README.md` 0/0/0, `docs/TREE.md` 0/0/0, `docs/GLOSSARY.md` 0/0/**1**, root `README.md` 0/0/0, `KANBAN.md` **1**/**1**/0. Every figure matches the build report, including its correction of the plan.

### The `### Dispatched findings checklist` — box by box

All 12 are ticked. Walked each for substance **and** for the truth of its cited evidence, because this cycle has already produced five findings where a box's substance was right and its cited evidence was false.

| Box | Substance | Cited evidence, re-derived |
|---|---|---|
| D1 | **Holds.** Four bullets landed at the four prescribed positions | `__all__ 37 \| root bullets 38`, `missing: []` — **reproduced** |
| D2 | **Holds.** `__version__` links `#joint-version-cut`, whose entry names it and reads `shipped (0.0.13)` | **Formula false, substitute correct and disclosed.** `git diff -- docs/SPECS/spec-006-public_surface-0_0_3.md` is `52 62`, not empty, and cannot be empty — R2 of this cycle rewrote that spec and the rewrite is uncommitted. The claim the box needs is that *R3* made no spec edit; the mtime substitute (`12:00:04`, predating the 12:50 first write) establishes it. Worker 2 named the swap rather than letting a later reader think the literal command was run. See item **E2** |
| D3 | **Holds.** Retirement recorded as done; spec-003 closing sentence verbatim; `is_complete False` | both greps → **0** and **0** — reproduced; spec-002's heading list independently confirmed |
| D4 | **Holds.** One sentence replaced; three survive byte-identically | `grep -c 'public_surface-0_0_3.md:1' KANBAN.md` → **0** — reproduced; the "exactly one replaced sentence" half re-derived by my own set difference against `db-before.sql` |
| D5 | **Holds.** Falsified clause gone; open question narrowed not closed; tail verbatim | both greps → **0** and **1** — reproduced |
| D6 | **Holds, and is the strongest box in the list.** | three `cmp` exit 0 and three `--check` exit 0 **independently re-run by me**; the three baseline diffs reproduced line-for-line; the disclaimer that `git diff` is unavailable is right for three of the four paths and Worker 2 corrected it for the fourth |
| D7 | **Holds.** Writing form ran, `--check` green, wide footprint pre-explained | `OK: 49 done cards have glossary links.` exit 0 — **re-run by me** |
| D8 | **Holds.** Audit ran read-only and reported | `len(__all__) 37 \| pin matches True`, both set differences empty — reproduced; `9`; no `## Current surface` / `## Package architecture`; `git status --short docs/README.md docs/TREE.md README.md` empty — all reproduced |
| D9 | **Holds.** All three directions swept, nothing dangles | 8/8/0/0 and 16/16/0/0 — reproduced; occurrence-count discipline confirmed (I re-took the inbound table with `grep -o … \| wc -l`) |
| D10 | **Holds.** Zero outside the board files and this cycle's artifacts | **Count now 4 in 2 files, not the reported 3.** Self-invalidated: the fourth hit is `bld-006-r3-…:700`, a line of Worker 2's own build report quoting the pattern, written after the measurement. Not a defect and not a sixth counting error — a genuinely time-dependent number that a report cannot state without changing. The substantive claim (zero in source, tests, or any standing doc) is exact |
| D11 | **Holds.** Archive complete and unchanged | `DONE-006-0.0.3 done 0.0.3 \| glossary_links 7`, `SpecDoc.path …`, CSV `8` lines and absent from `git status`, `check_spec_glossary` exit 0 — all **re-run by me** |
| D12 | **Holds.** Reported, never reverted | `git status --short` before/after quoted; `git log --stat -3` over the four paths returns `947f7494` as the most recent commit touching any of them, which predates this cycle, so nothing was swept in. **Re-derived:** HEAD is still `947f7494` |

**No box is ticked without a matching change, and no sub-check is silently unaddressed.** One box (D2) carries false cited evidence, and it is the only one; it is disclosed in the build report with a recommended replacement, which is the disposition `worker-3.md` asks for rather than a finding to hold the unit on.

### `import_spec_terms`' wider DB diff — re-classified at table granularity

Re-derived independently, and the first way I measured it was wrong, so both the method and the correction are recorded.

**Method note, worth carrying forward.** My first attempt loaded `db-before.sql` and `db-after.sql` into temp SQLite databases and re-dumped them for comparison. That round-trip produced **4 spurious `products_entry` residual rows** — rows whose text contains embedded newlines, tabs and quote characters, which do not survive `executescript` → `iterdump()` byte-identically. It briefly read as a concurrent writer having touched the products tables. **Retracted.** The correct instrument is to compare the raw dumps as text and to take a fresh dump the same way Worker 2 took its own. Corollary for a future pass: never round-trip a dump through `executescript` to compare it.

Measured correctly, comparing statement multisets over the raw dumps:

| Table | Statements differing | Attribution |
|---|---|---|
| `glossary_glossaryspecmention` | 1042 | step 6's `import_spec_terms` — **timestamp-only** |
| `kanban_cardglossaryterm` | 1042 | step 6's `import_spec_terms` — **timestamp-only** |
| `kanban_boarddoc` | 1 (pk 41) | **this pass**, step 4 |
| `kanban_carditem` | 3 (pks 1240 / 1260 / 1270) | **this pass**, step 5 |

- **2,088 statements differ; 2,084 of them are byte-identical once every `'YYYY-MM-DD HH:MM:SS.ffffff'` literal is normalised**, leaving a residual of exactly **4** — the one `BoardDoc` and the three `CardItem` rows. That is Worker 2's "2,084 rows ... a `modified`-only touch" reproduced exactly, with the two content tables it omitted from that figure accounted for separately as it also said.
- **No table gained or lost a row**: 9,856 statements on both sides, and per-table counts identical across `db-before.sql`, `db-after.sql`, and the live DB.
- **No concurrent writer's row appears anywhere in the diff**, which is the same fact step 3's empty baselines predicted.
- **A stronger fact than the build report claims:** a fresh `iterdump()` of the live DB taken by me is **byte-identical to `/tmp/dsf-r3-baseline/db-after.sql`** (`cmp` exit 0, both 11,224 lines). So the DB has not been written by anyone since 12:51, this pass's four rows are still exactly as it left them, and the classification above is the complete and current account of the DB diff.
- Card 6 untouched, verified live: `DONE-006-0.0.3`, `SpecDoc.path` archived, `glossary_links` 7, terms CSV absent from `git status`.

### Temp test verification

- `docs/builder/temp-tests/r3/KANBAN.md.w3pre`, `KANBAN.html.w3pre`, `GLOSSARY.md.w3pre` — copies of the three working-tree files taken **before** my first regenerate, which is what makes the hand-edit test (`render == working tree`) possible without relying on Worker 2's own `.pass1` copies.
- No temp *test* was written: there is no executable behavior in this diff to pin. Every verification in this review is a measurement over the rendered files, the DB, or source, and each is quoted with the command that produced it.
- **Disposition: kept for Worker 1's final verification, then deletable.** Nothing here is promotable to a permanent test, and nothing here caught a bug that would need one — the closest thing to a finding, L1, is a prose defect in a generated document that no test tree covers.
- `scripts/review_inspect.py` was **not run, and the skip is recorded with its reason** (`worker-3.md` `## Static helper use`): `BUILD.md` `### When to run the helper during build` triggers on changed `.py` files and this pass changed none, so there is no module to shadow and no repeated-literal or import-boundary evidence to gather. No shadow file was generated or read. `docs/shadow/` is not in this pass's writable set and was not written.

### Notes for Worker 1 (spec reconciliation)

**E1 — Escalated (Medium): `spec:17`'s "the per-feature entry that carries that name's status marker" is now literally false for two bullets this cycle wrote, in the same direction as the residue R2's review already escalated.** `spec:44` condition 3 asks only for "a bullet in the root re-export group ... linking a per-feature entry whose status marker reads `shipped`", and all five new bullets satisfy that — verified anchor by anchor and marker by marker above. But `spec:17` says something stricter about the same object: "Every bullet links **the per-feature entry that carries that name's status marker**." For `DjangoSchema` the linked entries carry the *policies'* markers, and for `DjangoMutationExecutionContext` the linked entry carries `DjangoMutation`'s; neither name has an entry, so neither has a marker of its own for any entry to carry. The two `DEFAULT_*` bullets are a milder instance — `#errorpolicy` and `#resourcepolicy` at least name the constant explicitly as root-exported alongside the dataclass.

Why this is escalated rather than blocking, and why it is not a new problem: the shape is pre-existing and licensed by practice — `RESOURCE_LIMIT_ERROR_CODE` and `ResourceLimitExceeded` both point at `#djangoresourcepolicyextension`, `aapply_cascade_permissions` shares `#apply_cascade_permissions`, and `global_id_for` / `decode_global_id` share one bullet — and `spec:76` explicitly licenses documenting a name "with the dotted path stated in the family's own entry". So the gate is again **stricter than the practice it describes**, which is the identical direction and the identical class as the `__version__` residue I escalated at R2 pass 2 and which R3 has now closed. It is a spec-wording question, R3 has no licence to touch a spec, and card 052 owns the entry-granularity call that would close it from the other side.

Resolution paths, for Worker 1 to pick between at final verification:

1. **Amend `spec:17` to admit the established many-names-to-one-entry shape** — e.g. "Every bullet links the per-feature entry that documents that name and carries its status marker; several names may share one entry, and a bullet whose name has no entry of its own links the entry that documents the behavior it wraps." This is reconciliation in this cycle's own sense (writing down what the glossary has always done) and it is the smaller edit.
2. **Leave `spec:17` as-is and let card 052 close it** by authoring `DjangoSchema` and `DjangoMutationExecutionContext` entries, after which both bullets link their own entries and the clause is true again. This defers a currently-false clause in a durable file, which is the posture `## The single-ownership law` clause 2 was invoked to end.
3. **Do nothing and record the divergence.** Weakest: it leaves a reconciled spec carrying a clause its own cycle's write falsified, which is D13's failure mode in miniature.

My non-binding lean, recorded so the alternative is on the table rather than to constrain the custodian: path 1, because the clause is describing a generated document whose convention is older than the clause, and because path 2 makes the spec's truth contingent on a beta-line card.

**E2 — Escalated (Low): adopt Worker 2's two plan-evidence corrections and its two plan-measurement corrections.** All four of its `### Notes for Worker 1` items are correct, and I re-derived each independently rather than accepting it:

1. **D2's evidence formula is unsatisfiable** — `git diff -- docs/SPECS/spec-006-public_surface-0_0_3.md` is `52 62`, not empty, because R2 of this cycle rewrote the spec and the rewrite is uncommitted. Confirmed. The recommended replacement wording is right; the substance of D2 (R3 made no spec edit) is established by the mtime and by my own reading of the spec, which still carries R2's `:44` and `:17` text unchanged.
2. **The em-dash / ASCII-hyphen mismatch is real** — the quoted string occurs **0** times in the spec-002 rationale, whose heading at `:503` carries an em dash. This is finding **L1** above; Worker 2's proposed shortening to `` `## The discharged deferral` `` is the right fix and is Worker 1's to apply, since the plan declared the text non-discretionary.
3. **`experimental` / `aspirational` are 1 each in `KANBAN.md`, not 0** — confirmed by occurrence count. Both hits are prose (`:80` describing a commented-out example schema block, `:1376` a card checklist item naming `# experimental` as a thing to sweep for), neither is a marker on a consumer-visible entry, and no correction is owed. The plan's step-10 figure of `0/0/0/0/0` is wrong and its D9 counterpart is right for the four docs D9 actually measured — a scope difference, not a regression.
4. **`CardItem.order` is not a rendered ordinal** — confirmed: `order` 1 / 8 / 11 render as the **1st / 6th / 9th** of 18 `#### Scope` bullets, because the order sequence is sparse. Nothing moved; only `text` changed. The plan's step-8 check as literally worded fails against a correct render.

**A plan-evidence defect correctly reported is good practice, and in all four cases the *implemented* behavior is right regardless** — which is the distinction the dispatch asked me to draw, and it holds for every one of the four. Worker 2 found four defects in the instrument it was handed and none in what it built.

**N3 — the pk-1240 widening: I accept the scope call, and here is the positive case rather than an absence of objection.** `### Maintainer decision 2`'s WIDENED block authorizes exactly one sentence in exactly this `CardItem`, and the write is exactly that: one sentence replaced by two, the rest byte-identical, `is_complete` untouched, no other card and no other file. Three things make it the right call rather than a tolerable one. First, the falsification is **caused by this pass** — pk 1240 asserted the roster gap that step 4 closed 90 seconds earlier — which makes it a defect in this cycle's output, not a deferral inherited from a prior one. Second, the replacement **narrows** the open question instead of closing it: `DjangoSchema`'s entry-granularity decision stays card 052's in the item's own words, so the card loses nothing it needs. Third, the alternative the plan itself offered as a fallback (revert the row, add a sweep item to card 052) would have published, on the board, a claim this cycle knew to be false — which is `## The single-ownership law` clause 2's exact prohibition, applied to a reference this cycle's own write falsified. **Outcome to record at final verification: the widening landed, and Worker 3 accepted it on scope.**

**N4 — growth events, all reported and none reverted.** Two are new since the build report was written: (a) `docs/review/rev-_cross_web_patches.md` has moved from `D` to `M` — the concurrent transport session restored and rewrote a file it also has open as `_cross_web_patches.py`; the other four `rev-*.md` deletions and the two untracked additions are unchanged, and the whole `docs/review/` escalation to the maintainer stands untouched. (b) `django_strawberry_framework/_cross_web_patches.py` (mtime `12:57:00`) and `examples/fakeshop/test_query/test_transport_api.py` (`12:57:43`) were both written **after** Worker 2's pass closed, so that session's working set is still moving. HEAD is still `947f7494`; nothing of this cycle's has been swept into a commit. Worker 0 to append (a) and (b) to the plan's growth list beside the fourth and fifth events. **Nothing in `docs/review/` or any `.py` file was read for content, touched, or reverted by this pass.**

**N5 — the count that will move under a later reader, flagged so it is not read as a defect.** D10's "3 hits in 2 files" is now 4, because the fourth hit is a line of Worker 2's own build report. A staged-anchor sweep run from inside an artifact that quotes the pattern cannot state its own result stably. Not worth changing the box; worth one clause at final verification so the sixth counting discrepancy of this cycle is not recorded as one.

**N6 — the DRY residue, stated once so it is not re-litigated.** Finding L2 (the `DjangoSchema` bullet restating both linked entries) is **not** to be fixed before card 052 authors the entry; trimming it now leaves the name with a gloss that documents nothing. Recorded as weighed, with the collapsed form the entry would enable.

### Review outcome

`review-accepted`.

Every High/Medium/Low finding is addressed, intentionally rejected with a reason, or escalated: **High none; Medium none blocking, one escalated as E1; Low two (L1 escalated as E2 item 2, L2 recorded as deliberately-not-yet-fixable with its reason)**. All 12 checklist boxes are ticked with matching changes, and the one box whose cited evidence is false (D2) is disclosed in the build report with a correct substitute and a recommended replacement. The public-surface check is clean, the documentation/release sanity check passes in full including its regenerate-and-source-in-the-same-pass rule, the byte-stability and diff-footprint claims were re-derived independently and reproduced exactly, the DB diff classifies to 2,084 timestamp touches plus this pass's four rows with no concurrent row in it, the archive is complete and unchanged, and the read-only half stayed read-only. Failability proofs, hot-path budget, and floor verification are not applicable by the plan's declarations, which I confirmed rather than accepted; the mandatory re-run floor is met by an empty set because no boundary in the diff meets it. `ruff` was correctly not run.

---

## Final verification (Worker 1)

Verified 2026-08-14 at HEAD `947f7494` (`git rev-parse --short HEAD` re-derived at the start and again at the close of this pass — unmoved from the plan's, the build report's, and the review's readings). Every number below was re-measured in this pass; where it differs from a number in a prior section, both are quoted and neither prior section is edited.

**What this pass did to the tree.** It ran the three renderers twice (the prescribed byte-stability instrument, which leaves the files byte-identical if the claim holds — proved below, not assumed), took one read-only `iterdump()`, and edited **two** files: one sentence in `docs/SPECS/spec-006-public_surface-0_0_3.md` and one appended `##` section in `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`, both recorded under `### Spec changes made (Worker 1 only)`. No DB write, no hand edit of any generated file, no `git checkout` / `restore` / `stash` / `worktree`, no commit, no branch, no `pytest` in any form.

- **Spec slice checklist:** this is a review round, so the audit target is `### Dispatched findings checklist` — 12 boxes, all `- [x]`. Audited box by box for substance **and** for the truth of the cited evidence below. Result: **12 hold on substance; 11 hold on cited evidence; 1 (D2) carries a false formula, disclosed by Worker 2 with a correct substitute.** No box un-ticked, none newly ticked, none silently un-addressed.
- **DRY check across this cycle's three items:** re-derived below. One accepted residue (L2), confirmed as deliberately not-yet-fixable; no new duplication.
- **Existing tests:** no focused `pytest` scope is applicable — this item's diff is four DB rows, three rendered documents, and two spec-side markdown files, none of which the suite executes. No `pytest` was run, with or without `--cov*`.
- **Spec reconciliation:** one edit was owed and made (E1, below).
- **Final status:** `final-accepted`.

### Spec status / header-line re-verification (mandatory every spawn)

Re-read lines 1-9 of `docs/SPECS/spec-006-public_surface-0_0_3.md` at this pass's own reading time rather than accepting the plan's:

- Line 1 is the title. **The spec still carries no `Status:` / target-release / owner / predecessor header block**, and never did; `## Problem statement` opens at `:5`. There is no status line to falsify, and the measurement is recorded rather than omitted so silence does not read as "not checked".
- **The H1 companion pointer at `:3` resolves.** It names `[rationale file][spec-006-rationale]`; the definition at `:154` reads `appx/spec-006-public_surface-0_0_3-rationale.md`; that path exists on disk and was re-verified resolvable by the link script below (`unresolved []`). Its three named subjects — the alignment problem's origin, the declined three-section README shape, and the release-gating judgement — are each an entry in the companion, and the companion's own new `##` section from this pass needs no new pointer because the sentence points at the file, never at a section list.
- `grep -nE 'not yet|remains to be|will be shipped'` → no match. No first-nine-lines claim is falsified by the build.

### The escalated Medium — E1, settled

**Decision: amend `spec:17`. Resolution path 1, and the measurement is what decides it rather than the lean.**

Re-derived first, because the finding's premise is a claim about a generated document and this cycle has already been wrong twice about that document's shape. Under `:17`'s wording as R2 left it — "Every bullet links the per-feature entry that carries **that name's** status marker" — I counted, over the **rendered** `docs/GLOSSARY.md`, every `## Public exports` bullet whose linked anchors reach no heading titled by the bullet's own lead name:

```text
bullets whose links do NOT reach an entry titled by the bullet's own name: 14 of 48
   DEFAULT_ERROR_POLICY           -> ['errorpolicy']
   DEFAULT_RESOURCE_POLICY        -> ['resourcepolicy']
   DjangoMutationExecutionContext -> ['djangomutation']
   DjangoSchema                   -> ['execution-resource-policy', 'production-error-policy']
   RESOURCE_LIMIT_ERROR_CODE      -> ['djangoresourcepolicyextension']
   ResourceLimitExceeded          -> ['djangoresourcepolicyextension']
   aapply_cascade_permissions     -> ['apply_cascade_permissions']
   __version__                    -> ['joint-version-cut']
   AsyncTestClient                -> ['testclient']
   Response                       -> ['testclient']
   GraphQLTestMixin               -> ['graphqltestcase', 'testclient']
   GraphQLTransactionTestCase     -> ['graphqltestcase']
   global_id_for                  -> ['relay-node-integration']
   login_mutation                 -> ['auth-mutations']
```

Three further measurements taken with it: **3** of the 48 bullets carry an unlinked *name* (the two this cycle wrote plus the pre-existing `global_id_for` / `decode_global_id`); **10** anchors are each the destination of 2-4 bullets (`testclient` 4, `djangoresourcepolicyextension` 3, `graphqltestcase` 3, seven more at 2); and **0** bullets reach no entry at all.

**This is why path 2 cannot work, and it is the fact Worker 3's escalation did not have.** Worker 3 framed the choice as two names lacking entries, which card 052 could close. It cannot: authoring `DjangoSchema` and `DjangoMutationExecutionContext` entries closes **2 of the 14** falsifications and leaves **12** standing, every one of them pre-existing convention rather than this cycle's output. So path 2 defers a false clause in a durable file to a beta-line card that would not make it true. Path 3 is D13's failure mode in miniature, as Worker 3 says. Path 1 is not merely the smaller edit; it is the only one that ends with a true sentence.

**Constraint-by-constraint, as the dispatch requires:**

- **Condition 3 at `:44` is byte-unchanged.** It still reads "the symbol carries a bullet in the root re-export group of `docs/GLOSSARY.md` `## Public exports`, linking a per-feature entry whose status marker reads `shipped`", and it still fails for `TestClient`, `DjangoDebugExtension`, and `login_mutation` — re-measured: all three are in the section, **none** is in the root re-export group, and none is in `__all__`. The gate's strength did not move.
- **The replacement can still fail, and against a named input.** A bullet reaching no entry at all fails it — which is exactly the `__version__` residue R2 escalated and R3 closed. Measured today: `unlinked bullets in the whole section: []`, so the document satisfies the amended sentence, and the sentence is satisfiable-not-vacuous because it was unsatisfied one pass ago.
- **No chronology, no amendment block, no "as of".** The edit is an in-place replacement of one sentence inside one line; the spec gains no narration about its own history. `BUILD.md` `## Spec rationale extraction` rule 1 is honoured by the pointer already at `:3` — the change record lives in the companion.
- **Single ownership.** The amended sentence states the rule and names *why* a gloss may carry the link (the entry serves several names, or documents the behavior the name wraps). It registers no name, no count, and no family, so it takes nothing the glossary or another spec owns. This is the same repair shape R2 used for the flat-list premise: a distinction, never an assertion about a shape the file lacks.
- **Corrective, not more than corrective**, so a late Worker 1 edit is the right instrument rather than `revision-needed`: it changes no contract Worker 2 implemented (the five bullets are untouched and remain byte-identical to the plan's fenced texts), and `worker-1.md` `## Spec custody` licenses exactly this — the build proved a spec sentence inaccurate.
- **The 7-anchor constraint survived the edit.** `:17` carries none of the seven carriers (they sit at `:19`, `:53`, `:108`); `check_spec_glossary` re-run **after** the edit prints `OK: 7 terms - all have glossary entries and at least one spec link.` exit 0.

**Rejected alternatives are recorded in the companion, keyed to the heading and anchor they serve** (`### `## Where the public surface is defined` — what a bullet's link can be required to reach`, under `[spec-006-surface]` and `[spec-006-reexport]`), together with the pattern note the dispatch asked for. Nothing about the change is narrated in the spec.

### The pattern, judged as a pattern

**Confirmed: three instances, one shape, and it is the shape that made this cycle necessary.** Re-derived from the artifacts rather than accepted from the finding:

1. The plan's premise that `## Public exports` is one flat root-export roster — `### Maintainer decision 2`'s own `CORRECTION` records it, and the section is four groups.
2. The documentation condition read as satisfied by every bulleted export, when one bullet (`__version__`) carried no link at all — R2's escalated Low, closed by R3 in the document rather than in the gate.
3. E1 above: a bullet's link required to reach its own name's entry, false for 14 of 48 bullets.

In all three the rule was right about what it should require and wrong about the artifact it was written over, because the artifact was described from its heading instead of measured. That is the same failure as the spec's original `docs/README.md` `## Current surface` / `## Package architecture` obligations (drift rows D5, D8, D17) — rules stated over a section that never existed, which is the root cause this cycle exists to correct. A rule of that kind is unenforceable in one direction only: it condemns conforming practice, so the practice reads as the defect and the rule reads as sound, which is precisely why such a rule survives review. **Recorded in the companion as a standing note in its own right**, with the test that separates a measured restatement from a relaxation: whether the replacement can still fail, and against which input. That test is what licensed path 1 here and what refused the `__version__` carve-out at R2.

### The two Lows — settled

**L1 — the ASCII-hyphen citation in `CardItem` pk 1260. DEFERRED, not routed, with two named targets in priority order.** Re-derived independently: `'## The discharged deferral - Visibility status retired by the spec-006 cycle'` occurs **0** times in `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`; the heading on disk at `:503` carries an em dash; the distinctive stem `The discharged deferral` occurs **2** times there and is unique to that record. Worker 3's severity is right, and Worker 2's disposition (report with a recommended replacement rather than edit plan-declared non-discretionary text) was correct.

Cost weighed honestly, as the dispatch requires. Routing it costs a Worker 2 pass, a Worker 3 re-review, and a Worker 1 re-verification for **one character** in one `CardItem.text`; and it costs them against a tree that produced **five** growth events inside this one cycle, with a DB write that can no longer be attributed against a pre-write regenerate-to-temp baseline of the kind that made R3's own write auditable — that instrument was consumed at 12:47 and cannot be re-taken for a write that lands after it. Against that: the defect degrades a citation rather than falsifying a claim, no reader is lost (the stem is unique and greppable), and the item is already inside an owned five-site sweep. **So: defer.** Targets, named rather than gestured at:

1. **The maintainer, at commit** — the cheapest correct route, since the DB write and the commit are already theirs. The exact change, adopting Worker 2's own proposal: in `CardItem` pk 1260's `text`, replace `` `## The discharged deferral - Visibility status retired by the spec-006 cycle` `` with `` `## The discharged deferral` ``, then regenerate `KANBAN.md` and `KANBAN.html`. One `str.replace`, `.save()` never queryset `.update()`, and the `KANBAN.md` footprint stays the same three lines.
2. **Card `TODO-ALPHA-052-0.1.0`'s five-site sweep**, if the maintainer declines — that card already owns this exact `CardItem` and will rewrite its neighbourhood.

Recorded in `### Hand-off to the final gate` and owed a line in the final gate's `### Deferred work catalog`. **I did not edit the DB**, which is outside this pass's writable set.

**L2 — the `DjangoSchema` bullet as a fourth site. Worker 3's disposition CONFIRMED, and the site count is right.** Re-verified: the construction-time fact is stated in the bullet, in `## Production error policy`, in `## Execution resource policy`, and in `django_strawberry_framework/schema.py::DjangoSchema`'s docstring — four sites, as Worker 3 counted. Trimming it now would leave the name a gloss that documents nothing and two foreign anchors with no stated relevance, which is strictly worse than the duplication; the structural fix is the entry card 052 owns, after which the bullet collapses to one line and the duplication disappears rather than being cut. **Not to be "fixed" before that entry exists.** The amended `:17` above is what makes the current shape conforming rather than tolerated, which is the honest state.

### The `### Dispatched findings checklist` — independent audit of all 12 boxes

Every box re-derived from the tree, not from Worker 2's or Worker 3's account. **Substance: 12/12 hold. Cited evidence: 11/12 true.**

| Box | Substance, re-derived by me | Cited evidence, re-derived by me |
|---|---|---|
| D1 | **Holds.** Four bullets present in the root group at the four prescribed positions (`DEFAULT_ERROR_POLICY` 3, `DEFAULT_RESOURCE_POLICY` 4, `DjangoMutationExecutionContext` 17, `DjangoSchema` 24 of the group) | **True.** `__all__ 37 \| root bullets 38`, `missing bullets: []` — reproduced |
| D2 | **Holds.** `__version__`'s bullet links `#joint-version-cut`; that heading exists at `docs/GLOSSARY.md:1057` its entry reads `**Status:** shipped (`0.0.13`)`, and its body names `__version__` in the version quintet | **FALSE FORMULA, correct substitute, and now superseded.** `git diff --numstat -- docs/SPECS/spec-006-public_surface-0_0_3.md` → `52 62`, not empty, and could not have been empty during this cycle (R2's rewrite of that file is uncommitted). Worker 2 disclosed the swap and took the mtime substitute; I confirm both. **This pass supersedes the substitute:** the spec is now edited by *me* rather than by R3, so the durable claim is the one in `### Spec changes made (Worker 1 only)` — R3's write set was four DB rows and three rendered files, and the spec's mtime `12:00:04` predates R3's first regenerate at `12:50:04` |
| D3 | **Holds.** pk 1260 states the retirement as done, names where the discharge is recorded, keeps the closing spec-003 sentence, `is_complete False` | **True.** `grep -oiE 'visibility[ -]status'` → **0** in spec-002 and **0** in spec-006; `grep -c 'spec-002-visibility'` in the spec-002 companion → **0**; spec-002's surviving `##` headings are `Purpose` / `Problem statement` / `Architecture decision` / `Shipped slices` / `Coordination with …` / `References` / `Implementation checklist` — no status-shaped section |
| D4 | **Holds.** pk 1270 no longer instructs against sweeping spec-006's two sites; carries no raw `path:NN` to spec-006 | **True.** `grep -c 'public_surface-0_0_3.md:1' KANBAN.md` → **0**; and `grep -c 'public_surface-0_0_3.md:[0-9]' KANBAN.md` → **0**, a stricter form of the same claim |
| D5 | **Holds.** pk 1240's falsified clause is gone and the entry-granularity question is narrowed, not closed | **True.** `grep -c 'are absent from the Public exports list' KANBAN.md` → **0**; `grep -c 'has no `DjangoSchema` entry' KANBAN.md` → **1** |
| D6 | **Holds, and I re-proved it rather than re-reading it.** | **True.** Two consecutive regenerates of all three docs: `cmp` exit 0 ×3 (`STABLE KANBAN.md` / `STABLE KANBAN.html` / `STABLE GLOSSARY`); all three `--check` forms print `is up to date.` exit 0; and the **hand-edit test** — my render against copies taken before my first regenerate — `cmp` exit 0 ×3, so no line of any of the three files is a hand edit. Footprint reproduced exactly: `docs/GLOSSARY.md` `5 insertions(+), 1 deletion(-)` in hunks `@@ -26,0 +27,2 @@` / `@@ -38,0 +41 @@` / `@@ -44,0 +48 @@` / `@@ -59 +63 @@`; `KANBAN.md` `4 4` with hunks at `:248`/`:314`/`:319`/`:322`; `KANBAN.html` `1 1` at `:97` |
| D7 | **Holds.** Writing form ran; the wide footprint is pre-explained | **True.** `import_spec_terms --check` → `OK: 49 done cards have glossary links.` exit 0 — re-run by me |
| D8 | **Holds.** The audit ran read-only and its findings reproduce | **True.** `len(__all__) 37 \| pin matches True`, `pin-only set()`, `all-only set()` (a literal-tuple identity check, not a count); `grep -c 'planned by TODO-' docs/TREE.md` → **9**; `docs/README.md` carries no `## Current surface` and no `## Package architecture`; the legend carries exactly five markers; `git status --short docs/README.md docs/TREE.md README.md` → empty |
| D9 | **Holds.** All three directions swept; nothing dangles | **True.** spec-006 **8** defs / 8 used / 0 undefined / 0 unused / 0 unresolved; companion **16 / 16 / 0 / 0 / 0** with all **12** fragment definitions slugging to real spec-006 headings; inbound table re-taken by occurrence count. Re-verified **after** my two edits, so the numbers above are this pass's, not R3's |
| D10 | **Holds on substance; the number is time-dependent and has moved again.** Zero hits in source, tests, `KANBAN.md`, `KANBAN.html`, `BACKLOG.md`, or any standing doc | **True as scoped.** My sweep finds **5 hits in 2 files** (`build-006-…:31`, `:307`; `bld-006-r3-…:426`, `:700`, `:811`) against Worker 2's 3 and Worker 3's 4. Every increment is a line of this artifact quoting the pattern. A sweep run from inside an artifact that quotes its own pattern cannot state a stable count; the substantive claim is exact and is the one the box makes. **Not a counting error and not un-ticked** |
| D11 | **Holds.** Archive complete and unchanged in all three directions | **True.** `DONE-006-0.0.3 done 0.0.3 \| glossary_links 7`; `SpecDoc.path docs/SPECS/spec-006-public_surface-0_0_3.md`; terms CSV `grep -c ''` → **8** (header + 7 anchor rows, matching `glossary_links`), absent from `git status`, mtime `2026-06-04 14:49:54`; `check_spec_glossary` exit 0; all three archived paths present; both generated `KANBAN.md` references to the archived spec (`:141`, `:4824`) read the archived path |
| D12 | **Holds.** Reported, never reverted | **True.** `git log --stat -2` over the four written paths returns `947f7494` (2026-08-10) as the newest commit touching any of them — this cycle's work is **not** swept in. HEAD re-derived `947f7494`. No `git checkout` / `restore` / `stash` / `worktree` in this pass either |

**Corrections to the record, made here because prior sections are never edited.** Four of Worker 2's `### Notes for Worker 1` items are defects in the **plan's** evidence formulas — my own writing — and all four are correct. Adopted as corrections to the plan's text, with the implemented behavior confirmed right in every case:

1. **D2's formula (`git diff … is empty`) is unsatisfiable**, and was from the moment R2 rewrote the spec. Confirmed: `52 62`. The claim the box needs is that *R3* made no spec edit; the mtime establishes it. My plan wrote a formula that could never come back true — the fifth instance this cycle of right substance behind false citation.
2. **The row-8 dash mismatch** is real and is L1 above; the plan declared the text non-discretionary, so the defect is the plan's and the deferral decision is mine.
3. **`experimental` / `aspirational` are 1 each in `KANBAN.md`, not 0/0/0/0/0.** Re-measured by me with `grep -oi … | wc -l`: `docs/README.md` 0/0, `docs/TREE.md` 0/0, `docs/GLOSSARY.md` 0/0, root `README.md` 0/0, `KANBAN.md` **1**/**1**. Both `KANBAN.md` hits are prose, neither is a marker on a consumer-visible entry, and no correction is owed. The plan's step-10 figure was wrong; its D9 counterpart was right for the four docs D9 measured. Scope difference, not a regression.
4. **`CardItem.order` is not a rendered ordinal.** Confirmed: `order` 1 / 8 / 11 render as the **1st / 6th / 9th** of 18 `#### Scope` bullets. Nothing moved; only `text` changed. The plan's step-8 spot-check as literally worded fails against a correct render.

**Worker 3's method correction is honoured and re-used.** Comparing raw `iterdump()` dumps as text, never round-tripping through `executescript`: my own fresh read-only `iterdump()` of the live DB is **byte-identical to `/tmp/dsf-r3-baseline/db-after.sql`** (`cmp` exit 0, both **11,224** lines). So the DB has not been written by anyone since R3's pass, this cycle's four rows stand exactly as it left them, and the review's table-granularity classification (2,084 timestamp-only touches plus this pass's four rows, no table gaining or losing a row, no concurrent writer's row anywhere in the diff) is the current and complete account.

**Worker 3's disjointness proof is re-confirmed, which is what makes the mixed diff safe to hand the maintainer.** `git diff -U0 -- KANBAN.md` shows four changed lines: `:248`, `:314`, `:319`, `:322`. Line `:248` is a card item about `tests/types/test_base.py` and a `convert_relation` comment — a different card, a different subject, and read at both sides of the diff it is the concurrent card-wrap's. `:314` / `:319` / `:322` are this cycle's three `CardItem` rewrites. **The two sets are disjoint**, and the whole `docs/GLOSSARY.md` diff is this cycle's (that path was clean at baseline — Worker 2's CORRECTION to the dispatch's premise, which I confirm).

### Glossary outcome — re-derived from the rendered document

```text
__all__ 37 | root bullets 38
missing bullets: []
bullets not in __all__: ['SerializerMutation']
section bullets: 48
unlinked bullets in the whole section: []
root group span: docs/GLOSSARY.md:26-62 | section: :22-85
```

Exactly the expected `37 / 38 / [] / ['SerializerMutation'] / []`. Every anchor referenced anywhere in the section resolves: **41** distinct anchors, **0** dangling, checked with a markup-rendering slugger over the rendered file rather than by eye. The six anchors the five new bullets point at all carry a version-stamped `shipped` marker, which is what condition 3 reads: `#errorpolicy` `shipped (0.0.14)`, `#resourcepolicy` `shipped (0.0.14)`, `#production-error-policy` `shipped (0.0.14)`, `#execution-resource-policy` `shipped (0.0.14)`, `#djangomutation` `shipped (0.0.11)`, `#joint-version-cut` `shipped (0.0.13)`; `#djangoschema` and `#djangomutationexecutioncontext` are confirmed **absent**, which is why those two bullets leave the name unlinked. All five rendered bullet lines are **byte-identical to the plan's five fenced `text` blocks** (`block in glossary_text` → True ×5, lengths **158 / 170 / 313 / 357 / 128** in characters — a byte-length reading gives 160/172/315/359/130 because each carries one three-byte em dash, which is worth stating so the next reader does not record a sixth discrepancy).

**Condition 3 as written is satisfied by exactly the right set, and still fails for the right names.** All 37 `__all__` names carry a root-re-export-group bullet linking a `shipped`-marked entry. `TestClient`, `DjangoDebugExtension`, and `login_mutation` are each documented **in the section** and **absent from the root re-export group** — so condition 3 fails for all three, exactly as `:44`'s second sentence intends, and none is in `__all__`. Section shape intact: **four** groups in order (root roster `:24`, `extensions` `:65`, `testing` `:69`, `auth` `:81`), no group added, moved, or demoted, no listing for `views` / `routers` / `middleware.debug_toolbar` (card 052's, per the plan's `CORRECTION`); `## Status legend` at `:12-20` still renders **before** `## Public exports` at `:22` and carries all five markers including `alpha constraint`; the `SerializerMutation` bullet still says why it sits outside `__all__`.

### Scaffold and rule-27 gates on every durable file this cycle touched

- `uv run python scripts/check_trailing_commas.py --check KANBAN.md docs/GLOSSARY.md docs/SPECS/spec-006-public_surface-0_0_3.md docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md docs/builder/bld-006-r3-doc_completion_archive.md docs/SPECS/spec-002-optimizer-0_0_2.md docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` → **exit 0**, re-run after both of my edits.
- **All 10 canonical group headers present and positional** in both spec-006 files: `Root`, `docs/`, `docs/SPECS/`, `docs/builder/`, `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`, `.venv/`, `External`, under the single `<!-- LINK DEFINITIONS -->` block.
- **Every link-definition target is on disk**, both files, measured after my edits: `unresolved []`, `undefined []`, `unused []`.
- **No raw `path:NN` outside the `bld-006-*` artifacts.** `grep -oEc '[a-zA-Z_/.-]+\.(py|md|csv):[0-9]+'` → **0** in the spec, **0** in the companion; `grep -c 'public_surface-0_0_3.md:[0-9]' KANBAN.md` → **0**. `AGENTS.md` rule 27 is preserved by removal, not by rewriting one raw ref into another.
- **One `--check` failure exists tree-wide and it is not this cycle's file.** An unscoped `uv run python scripts/check_trailing_commas.py --check` reports `1 layout violation`, in `.claude/projects/-Users-riordenweber-projects-django-strawberry-framework/memory/one-spec-owns-each-feature.md`, which `git check-ignore` confirms is **git-ignored** at `.gitignore:170` and is another session's agent-memory file, not a repository document. Reported, not fixed, not read for content beyond the tool's own message. The final gate should expect it.

### The 7-anchor constraint and the card chain

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` exit 0. Run **after** my spec edit, which is the point of running it at all; `:17` carries none of the seven carriers (`:19`, `:53`, `:108` do), so no re-siting was needed, and the result proves it rather than the reasoning.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` (read-only form) → `OK: 49 done cards have glossary links.` exit 0.
- Card 6 unchanged: `DONE-006-0.0.3`, status `done`, target `0.0.3`, `SpecDoc.path docs/SPECS/spec-006-public_surface-0_0_3.md`, `glossary_links` **7**.
- Terms CSV byte-unchanged: **8** lines (header + 7 anchor rows, matching `glossary_links` exactly), **absent from `git status --short`**, mtime `2026-06-04 14:49:54`.

### The archive, complete in all three directions

- **To spec-006.** Inbound occurrence counts (occurrences, never matching lines), measured this pass: `KANBAN.md` 13, `KANBAN.html` 12, `appx/spec-002-…-rationale.md` 13, `appx/spec-006-…-rationale.md` 53, `appx/spec-007-…-rationale.md` 6, `appx/spec-005-…-rationale.md` 1, `spec-005-django_type_contract-0_0_3.md` 1, spec-006 itself 4, plus prior and concurrent cycles' builder artifacts and two `docs/review/` files. `spec-005:89` remains the **only** inbound reference from another spec, and R2 settled it by measurement (the by-title citation survives at `spec-006:102`, still inside `### Status-marker vocabulary`), so `spec-005` was correctly never edited. The spec-007 cycle's files and the `docs/review/` files are **reported and not edited**; `## The single-ownership law` clause 3's licence is spent.
- **From spec-006.** 8 definitions, 8 used, 0 undefined, 0 unused, all 8 resolving on disk (7 × `../GLOSSARY.md#…` plus `appx/spec-006-…-rationale.md`).
- **From the rationale, at `docs/SPECS/appx/` depth.** 16 definitions, 16 used, 0 undefined, 0 unused, all resolving; all **12** fragment-bearing definitions slug to real spec-006 headings (`#decision-for-003` included — a dotted version slugs to `003`). Depth conventions correct for `appx/`: `../../builder/BUILD.md` for a `docs/`-tree target, `../spec-006-….md` for a `docs/SPECS/` sibling, a bare filename for an `appx/` sibling. Re-measured **after** my append, which added no definition and consumed only existing ref-ids.
- **Staged-anchor sweep.** `grep -rEn 'TODO\(spec-006|TODO-(ALPHA|BETA|STABLE)-006' .` → 5 hits, both files this cycle's own artifacts. Zero in source, tests, `KANBAN.md`, `KANBAN.html`, `BACKLOG.md`, or any standing doc. Card 006 is `DONE-006-0.0.3`, so no `TODO-ALPHA-006` form should exist and none does.

### DRY check across R1, R2, and R3

- **No new duplication.** R3 added no script, helper, constant, or indirection; the four reusable pieces it needed (`scripts/_kanban_lib.py::configure_django` plus the three renderers) already existed and were reused unmodified.
- **The cycle's recurring DRY defect did not recur in my edit.** `:17`'s replacement names the rule and its reason and reproduces nothing the glossary or another spec owns; the companion entry states the measurement once and points at the heading it serves. My own memory's standing warning — *naming a claim costs more bytes than quoting it, and that is the right trade* — is the reason the spec gained **145 bytes on 0 lines** rather than a paragraph.
- **One accepted residue, confirmed not fixed:** L2. And the accepted near-duplication the plan recorded (`ErrorPolicy` / `ResourcePolicy` bullets ending "exported alongside `DEFAULT_*`") is still byte-unchanged, correctly — the clause states the export pairing, which is a fact and not a restatement.

### Failability, fail-open, hot path, floor, tests — declared, not omitted

- **Failability proofs: not applicable, with the reason.** `BUILD.md` `### What needs a proof, and what does not` scopes proofs to new boundaries, guards, gates, and rejection paths in **executable code**. This item's entire diff is four DB rows, three rendered documents, and two markdown files. There is no guard to remove, no comparison to invert, no lock to move, and no permissive value to return, so there is **no boundary a proof could be missing for** — the empty set is legal by the rule's own terms, not a sampling gap. **Boundaries added: none.**
- **Fail-open shapes: none possible.** No expression, clamp, `getattr` default, `or` fallback, `except`, or coercion exists anywhere in this diff to carry one. Read the diff for the catalogued shapes rather than inferring from a green suite: there is no executable line in it.
- **Hot path: none.** Nothing in the diff runs per request, per resolver, per row, per connection, or per outbound message. The three renderers are build scripts; the ORM writes were one-shot. No number is owed, so none is missing.
- **Floor-verification scope: none**, per the plan's declaration, which I confirm: no Django / Strawberry / channels integration seam, no source, no tests, no schema construction. `git diff --numstat -- '*.py'` lists only the concurrent transport session's three files.
- **No focused test run is applicable**, and none was run. `AGENTS.md` "Add tests in the same change as code" has no code to attach a test to; the cycle is source-read-only and `tests/base/test_init.py` is explicitly read-only. **No `pytest` in any form, and never `pytest --cov*`.** The verifications standing in for it are the three `cmp`s, the three `--check` forms, the hand-edit test, `check_spec_glossary`, `import_spec_terms --check`, the scoped `check_trailing_commas --check`, the roster script, and the `iterdump()` comparison — each quoted above with its result.

### Summary

R3 closed the last documented-surface gap this spec's own gate creates and left the archive verified rather than moved. In the DB: four bullets added to `docs/GLOSSARY.md` `## Public exports`' root re-export group (`DEFAULT_ERROR_POLICY`, `DEFAULT_RESOURCE_POLICY`, `DjangoMutationExecutionContext`, `DjangoSchema`) and one rewritten (`__version__`, which gained a link and therefore a marker), so all 37 `__all__` names now satisfy condition 3 for the first time and no bullet in the 48-bullet section is unlinked; three `CardItem` rows on card `TODO-ALPHA-052-0.1.0` rewritten — two discharging the cross-spec retirement R2 performed, one correcting a board claim this cycle's own write falsified — with `is_complete` ticked on none of them and the entry-granularity question deliberately left open. The three rendered documents were regenerated, never hand-edited, and proved byte-stable across two consecutive regenerates and against a hand-edit test. The archive is complete in all three directions and unchanged: card 6 `DONE-006-0.0.3`, `SpecDoc.path` archived, 7 glossary links matching a byte-unchanged 7-row terms CSV.

Final verification added one spec correction and one companion entry. `spec:17` required every export bullet to link its own name's entry, which is false for **14 of the section's 48 bullets** — only 2 of them this cycle's, 12 of them long-standing convention; the sentence now requires a bullet to reach a per-feature entry carrying the marker the name is documented under, by a link on the name or in its gloss, which the document satisfies and which still fails for a bullet reaching nothing. Condition 3 at `:44` is byte-unchanged and still fails for `TestClient`, `DjangoDebugExtension`, and `login_mutation`. The companion records the rejected alternatives and the pattern behind three of this cycle's corrections — a rule written stricter than the practice it describes, which is the same failure as the undischargeable `docs/README.md` obligations that made this cycle necessary.

### Spec changes made (Worker 1 only)

1. **`docs/SPECS/spec-006-public_surface-0_0_3.md:17`** (one sentence, in place; the file is **168 lines before and after**, so no anchor moved and no unreviewed line moved; 15,661 → 15,806 bytes, +145). Trigger: R3's Worker 3 review, escalated Medium **E1**. Reason: the sentence required every `## Public exports` bullet to link the per-feature entry carrying *that name's* status marker, which is false for 14 of the section's 48 bullets — a rule stated over a generated document without measuring it. Replaced by the same requirement stated over what the document does: a bullet reaches a per-feature entry carrying the marker the name is documented under, by a link on the name or inside its gloss when that entry serves several names or documents the behavior the name wraps. The bullet-versus-group distinction is preserved verbatim, condition 3 at `:44` is untouched, and the requirement remains falsifiable (a bullet reaching no entry fails it — the `__version__` residue R2 escalated).
2. **`docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md:698-763`** (appended `##` section `A rule stated over an artifact nobody measured`, with two `###` entries; 734 → 801 lines, 52,621 → 57,777 bytes; append-only, no prior line touched, no new link definition added — it consumes the existing `[spec-006-surface]` and `[spec-006-reexport]` ids). Trigger: the same finding, plus the dispatch's instruction to judge the pattern. Reason: `BUILD.md` `## Spec rationale extraction` requires the change, its rejected alternatives, and the claim the spec may no longer make to live here keyed to the heading and anchor they serve, and requires the spec itself to carry no chronology. Records the 14-of-48 measurement, the three rejected paths with the reason each lost (letting card 052 close it loses on measurement — it would close 2 of 14), the claim the spec no longer makes, and the standing note that three of this cycle's corrections share one shape with the spec's original undischargeable README obligations.

**Deferred, with the target named** (`docs/builder/ARTIFACT.md` requires a reason or `revision-needed`, and no box is left silently un-ticked — all 12 are `- [x]` and all 12 hold on substance):

- **L1, the ASCII-hyphen citation in `CardItem` pk 1260** → the **maintainer at commit** (a one-character `str.replace` plus a regenerate, exact strings given above), or failing that **card `TODO-ALPHA-052-0.1.0`'s five-site sweep**, which already owns this `CardItem`. A `DB text` fix belongs to a Worker 2 pass, and routing one costs a full builder-plus-reviewer loop for one character against a tree that produced five growth events inside this cycle; the defect degrades a citation whose stem is unique and greppable rather than falsifying a claim. Not edited here: the DB is outside this pass's writable set.
- **L2, the `DjangoSchema` bullet's fourth statement of the construction-time fact** → **card 052**, on authoring the entry, after which the bullet collapses to one line and the duplication disappears. Confirmed as deliberately not-yet-fixable, not deferred for convenience.
- **D2's evidence wording in the plan** → **Worker 0**, who owns `docs/builder/build-006-public_surface-0_0_3.md`. Three further plan corrections (the `experimental` / `aspirational` counts, the `CardItem.order`-versus-ordinal spot-check, and the row-8 dash) are recorded above for the same owner. All four are defects in evidence formulas I wrote; the implemented behavior is right in every case.

### Hand-off to the final gate

**Baseline exception the gate must honour**, recorded here because `BUILD.md` `## Final test-run gate` only honours a plan-declared one and this is its live restatement. `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree. **Four rendered/DB paths this cycle wrote** (`examples/fakeshop/db.sqlite3`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`) and **six source/test/review files two other sessions own** are dirty: `django_strawberry_framework/_boundary_ordering.py`, `django_strawberry_framework/_cross_web_patches.py`, `django_strawberry_framework/middleware/request_body.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py`, and `docs/review/rev-_cross_web_patches.md` (now `M` where it was `D`). **A failure attributable to any of the six is reported and does not block `final-accepted`**, does not route back through a residual item's loop, and is never fixed or reverted here. The gate still records every command's real result — the exception governs what a result blocks, never whether it is reported honestly. Expect one additional non-blocking finding: an unscoped `check_trailing_commas --check` flags a **git-ignored** agent-memory file under `.claude/`, which is not a repository document.

**Deferred items, each with its target:**

| Item | Target | What is owed |
|---|---|---|
| L1 — pk 1260 quotes the discharge heading with an ASCII hyphen, so the quoted string greps to 0 | **maintainer at commit**, else **card 052**'s sweep | replace the quoted heading with `` `## The discharged deferral` `` in `CardItem` pk 1260's `text` via the ORM (`.save()`, never `.update()`), then regenerate `KANBAN.md` and `KANBAN.html` |
| L2 — the `DjangoSchema` bullet is a fourth site for its two linked entries' construction-time fact | **card 052** | author the `DjangoSchema` entry; the bullet then collapses to one line. Do not trim before then |
| `DjangoSchema` / `DjangoMutationExecutionContext` entry granularity | **card 052** (`### Maintainer decision 2`'s WIDENED block) | the open question is recorded on `CardItem` pk 1240 and was deliberately narrowed, never closed |
| Group listings for `views` / `routers` / `middleware.debug_toolbar` in `## Public exports` | **card 052** (the plan's `CORRECTION`) | explicitly not R3's; the section's four groups are correct as they stand |
| Card 052's sweep is **five** sites, not four | **card 052**'s closeout | `bld-003-final.md` item 7 names `KANBAN.md:314` as the fifth; R3 has already rewritten it for a different reason |
| Four plan-evidence / plan-measurement corrections (D2's formula, the row-8 dash, the `experimental` / `aspirational` counts, `order` versus rendered ordinal) | **Worker 0** | the plan is Worker 0's file; the corrections are recorded above verbatim enough to apply |
| Five deleted committed `docs/review/rev-*.md`, one of which is now `M` | **maintainer** | escalated by Worker 0 at the cycle's second growth event; content is safe at `947f7494`. No worker restores it |
| Growth events 4-7 (`bld-007-r3-…`, `_cross_web_patches.py`, `rev-_cross_web_patches.md` `D`→`M`, the post-pass transport writes) | **Worker 0**, to append to the plan | reported by three passes, reverted by none |

**Mixed-diff facts the maintainer needs at commit:**

- **`docs/GLOSSARY.md` is entirely this cycle's.** That path was **clean** at R3's start (Worker 2's CORRECTION to the dispatch's premise, which Worker 3 and I both confirm), so `git diff` is a valid instrument for it: `5 insertions(+), 1 deletion(-)`, four hunks, five bullet lines.
- **`KANBAN.md` is mixed and the split is exact.** Four changed lines: `:248` is the concurrent card-wrap's (a card item about a `convert_relation` comment in `tests/types/test_base.py` — a different card and a different subject), and `:314` / `:319` / `:322` are this cycle's three `CardItem` rewrites. **Disjoint**, re-confirmed this pass from both directions: the surviving pre-write regenerate-to-temp baseline at `/tmp/dsf-r3-baseline/KANBAN.md` shows only the three, while `git diff` shows four.
- **`KANBAN.html` is one line**, `:97`, the embedded data block (+230 bytes). The hand-edited Vue shell is untouched. The `namespace='glossary'` `BoardDoc` is not embedded in the HTML, so that line is the three card-052 bullets and nothing glossary-side.
- **`examples/fakeshop/db.sqlite3`** carries this cycle's four rows (`BoardDoc` 41; `CardItem` 1240 / 1260 / 1270) plus a `modified`-timestamp touch on 2,084 rows across `glossary_glossaryspecmention` and `kanban_cardglossaryterm` from the writing `import_spec_terms`. **No table gained or lost a row, and no concurrent writer's row is in the diff.** Compare `iterdump()` semantics, never file bytes, and never round-trip a dump through `executescript` to compare it — that fabricates differences. A fresh read-only `iterdump()` taken this pass is byte-identical to R3's post-write dump (11,224 lines), so nobody has written the DB since.
- **The two spec-side files** (`docs/SPECS/spec-006-public_surface-0_0_3.md`, `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`) carry R1's and R2's work plus this pass's two edits. The companion is untracked and new; the spec's diff against HEAD is `52 62`, which is why D2's "`git diff` is empty" formula was never satisfiable during this cycle.
- **Not swept in.** HEAD is `947f7494`, unmoved through all four passes. `git log --stat -2` over the four written paths returns `947f7494` (2026-08-10) as the newest commit touching any of them, so every write of this cycle is still uncommitted and attributable. `docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv` is absent from `git status` and must stay so.
- **Nothing was reverted, restored, or checked out**, in any pass, for any reason.

### Review outcome

`final-accepted`.
