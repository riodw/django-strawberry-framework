# Build: Slice 9 — home two open findings on card 052 before this cycle's artifacts are deleted

Spec reference: none. This slice implements the maintainer's post-final-gate fence amendment in
[build-031][build-031] `### Fence amendment (maintainer, post-final-gate)` item 2 ("Kanban DB edits
are authorized"), extended to the two findings that would otherwise die with this cycle's
`bld-031-*` scratchpads ([AGENTS.md][agents] rule 27).
Build plan: [build-031][build-031].
Status: final-accepted

Closed by **procedural closure** ([BUILD.md][build-md] `### Procedural-closure slices`): one Worker 1
pass, one combined Plan + Final-verification block, `Status: final-accepted` set directly. No Worker 2,
no Worker 3. The change is one DB field plus one DB row plus the two renders that are the completion of
that DB edit ([BUILD.md][build-md] `### Generated docs are DB-backed: edit the DB, then regenerate`).

---

## Plan (Worker 1) + Final verification (Worker 1)

### Why this slice exists

Two genuinely-open findings lived only in this cycle's per-cycle scratchpads, which close with the
cycle. Both are documentation-consistency debt, which is the whole subject of
`TODO-ALPHA-052-0.0.16 - Alpha documentation-debt discharge`. This slice homes them on card 52 so the
scratchpads can be deleted without loss.

- **Item A** — a false remediation-tail attribution in `docs/SPECS/spec-032-full_relay-0_0_9.md`,
  recorded as a NEW `scope` bullet.
- **Item B** — the stale three-section census in `CardItem` pk 1278, re-measured and corrected.

### Fence

- **In fence:** `examples/fakeshop/db.sqlite3` (one field on one row, plus one new row),
  [KANBAN.md][kanban], [KANBAN.html][kanban-html], and this artifact.
- Nothing else was written. `docs/SPECS/spec-032-full_relay-0_0_9.md` was **read only** — repairing it
  is a future `032` cycle's call and is explicitly out of this slice's scope. No `.py` file, no other
  spec or companion, no `docs/GLOSSARY.md`, `docs/TREE.md`, `CHANGELOG.md`, and none of the agentflow
  standing docs. No `bld-031-*` artifact was deleted.
- No card renumber, no status change, no row deleted, no reset / re-migrate / re-seed / `git checkout`
  of the DB. Nothing staged, nothing committed, no branch.

### Working-tree baseline (re-read at pass start)

```text
 M KANBAN.html
 M KANBAN.md
 M django_strawberry_framework/types/definition.py
 M django_strawberry_framework/types/relay.py
 M docs/SPECS/spec-031-globalid_encoding-0_0_9.md
 M docs/SPECS/spec-032-full_relay-0_0_9.md
 M examples/fakeshop/db.sqlite3
?? 0_0_14.md
?? docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md
?? docs/builder/bld-031-*.md  (9 artifacts)
?? docs/builder/build-031-globalid_encoding-0_0_9.md
```

`KANBAN.md`, `KANBAN.html` and `examples/fakeshop/db.sqlite3` were already `M` at pass start — that is
Slice 7's pk-1243 edit, proved below by an `iterdump()` diff against HEAD showing exactly that one row.
Both renderers were **in sync with the DB before any edit**:

```shell
uv run python scripts/build_kanban_md.py --check    # "KANBAN.md is up to date."   exit 0
uv run python scripts/build_kanban_html.py --check  # "KANBAN.html is up to date." exit 0
```

`0_0_14.md` is a concurrent session's untracked file; the three `consumers.py` /
`utils/sessions.py` / `tests/test_consumers.py` paths from the cycle's baseline-dirty list have since
been committed by that session. Neither is touched here ([AGENTS.md][agents] rule 34).

---

## Item A — the `spec-032` false remediation-tail attribution

### Every claim verified against source, not accepted

| Claim | Verified how | Result |
|---|---|---|
| `_RELAY_NODE_GATE_INHERIT_TAIL` is the `Meta.connection` tail | `grep -n "_RELAY_NODE_GATE_INHERIT_TAIL\|or remove the key" django_strawberry_framework/types/base.py`, then read each compose site | Constant is ``"or inherit `relay.Node` directly."``; `_validate_connection` composes `_RELAY_NODE_GATE_LEAD` + that constant. **Holds** |
| `"or remove the key."` is the `Meta.relation_shapes` tail | same grep; the literal is **inline**, not the constant | Only compose site is `_validate_relation_shapes`. **Holds** |
| `spec-032` line 389 states the `relation_shapes` message correctly | `sed -n '383,395p' docs/SPECS/spec-032-full_relay-0_0_9.md` | `### Decision 7` quotes `... or remove the key`. **Holds — the spec contradicts itself** |
| the phrase was never in `spec-030`, before or after its rationale move | see the three-way proof below | **Holds** |
| the defect is pre-existing, not induced by this cycle | `git show HEAD:…` byte checks below | **Holds** |

### The population is THREE sites, not one

The handed lead named `spec-032` line 87. A tree-wide search for the shortest distinctive token found
two more:

```shell
grep -rn "remove-the-key" . --include='*.md' --include='*.py' | grep -v '/docs/builder/bld-'
```

```text
tests/types/test_base.py:551:    add-``relay.Node``-or-remove-the-key remediation (spec-032).
docs/SPECS/spec-032-full_relay-0_0_9.md:87:  ... rejected with the add-`relay.Node`-or-remove-the-key remediation ([`spec-030`][spec-030] Decision 8).
docs/SPECS/spec-032-full_relay-0_0_9.md:258:- [`Meta.connection`]... with the add-`relay.Node`-or-remove-the-key remediation (shipped; re-affirmed).
```

- `docs/SPECS/spec-032-full_relay-0_0_9.md` #"Re-affirmation coverage for the two already-shipped
  diagnostics" — the `## Slice checklist` Slice 1 sub-bullet.
- `docs/SPECS/spec-032-full_relay-0_0_9.md` #"remediation (shipped; re-affirmed)" — the
  `### Error shapes` entry. **Not in the handed lead.**
- `tests/types/test_base.py::test_connection_key_requires_relay_node` — the **docstring** claims it
  "pins the full documented add-``relay.Node``-or-remove-the-key remediation", while the assertion
  three lines later reads ``assert "add `relay.Node` to `Meta.interfaces` or inherit `relay.Node`
  directly." in message``. The assertion is right; the prose describing it is wrong. **Not in the
  handed lead.**

Each citation substring was checked unique before use:

```shell
grep -cF "Re-affirmation coverage for the two already-shipped diagnostics" docs/SPECS/spec-032-full_relay-0_0_9.md  # 1
grep -cF "remediation (shipped; re-affirmed)"                             docs/SPECS/spec-032-full_relay-0_0_9.md  # 1
grep -cF "### Decision 7"                                                 docs/SPECS/spec-032-full_relay-0_0_9.md  # 1
grep -cF "a connection field requires a Relay-Node-shaped DjangoType"     docs/SPECS/spec-030-connection_field-0_0_9.md  # 1
```

### The `spec-030` attribution is false — proved three ways, not asserted

1. **Whole history of the file.** `git log --all -S 'or remove the key' -- docs/SPECS/spec-030-connection_field-0_0_9.md docs/spec-030-connection_field-0_0_9.md` returns **no commits**. The phrase
   has never entered or left that file in any revision, under either path.
2. **Immediately before the rationale move.** `spec-030`'s rationale extraction is commit `6b3e1c82`.
   `git show 6b3e1c82^:docs/SPECS/spec-030-connection_field-0_0_9.md | grep -c "or remove the key"` →
   **0** (file 138,023 bytes); the post-move blob is 138,692 bytes and its only quoted remediation tail
   is `docs/SPECS/spec-030-connection_field-0_0_9.md` #"a connection field requires a Relay-Node-shaped
   DjangoType", which ends ``or inherit `relay.Node` directly``.
3. **The companion.** `grep -n "remove the key" docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`
   → no match. The phrase is in neither half of the pair.

Additionally, the cited `spec-030` Decision 8 (`sed -n '374,387p'`) states the `Meta.connection`
Relay-Node rejection but **quotes no remediation tail at all** — so `spec-032` did not mis-copy
`spec-030`, it invented a tail and attributed it.

### Pre-existing, not induced by this cycle

```shell
git show HEAD:docs/SPECS/spec-032-full_relay-0_0_9.md | grep -c "remove-the-key"   # 2
git show HEAD:tests/types/test_base.py            | grep -c "remove-the-key"       # 1
git show HEAD:docs/SPECS/spec-032-full_relay-0_0_9.md | sed -n '87p' \
  | grep -o "rejected with the add-.relay.Node.-or-remove-the-key remediation"     # matches
git diff -- docs/SPECS/spec-032-full_relay-0_0_9.md | grep -c "add-.relay.Node.-or-remove-the-key"  # 0
```

All three sites are byte-identical at HEAD, and the working-tree diff on `spec-032` (Slices 6 and 8)
touches none of them. Nothing this cycle did created or moved the phrase.

### The new row — full text

`CardItem` **pk 1409**, card 52, section `scope`, order **52**, 2,525 bytes:

```text
`docs/SPECS/spec-032-full_relay-0_0_9.md` attributes the wrong remediation tail to the `Meta.connection` Relay-Node gate, in two places, and one test docstring repeats the same false sentence. Measured 2026-08-26. The spec's `## Slice checklist` Slice 1 re-affirmation sub-bullet (`docs/SPECS/spec-032-full_relay-0_0_9.md` #"Re-affirmation coverage for the two already-shipped diagnostics") and its `### Error shapes` entry (same file, #"remediation (shipped; re-affirmed)") both say `Meta.connection` on a non-Relay-Node type is rejected with the add-`relay.Node`-or-remove-the-key remediation. The shipped message says no such thing. `django_strawberry_framework/types/base.py::_validate_connection` composes `_RELAY_NODE_GATE_LEAD` with `_RELAY_NODE_GATE_INHERIT_TAIL`, which is ``or inherit `relay.Node` directly.``; the bare `or remove the key.` tail belongs to `django_strawberry_framework/types/base.py::_validate_relation_shapes` and to nothing else, and the two are deliberately different byte shapes - which is why one is a named constant and the other stays inline. The spec also contradicts itself: its own `### Decision 7` states the `Meta.relation_shapes` message correctly, so one document carries both the true tail and the false one. And it mis-cites its source - `spec-030` has never carried the phrase in any revision, before or after its rationale extraction, and the only remediation tail spec-030 ever quotes is `docs/SPECS/spec-030-connection_field-0_0_9.md` #"a connection field requires a Relay-Node-shaped DjangoType", which ends ``or inherit `relay.Node` directly``. The third site is `tests/types/test_base.py::test_connection_key_requires_relay_node`, whose assertion pins the correct string while its docstring claims it pins the add-`relay.Node`-or-remove-the-key remediation - so the one instrument that could have caught the spec describes itself falsely. This is not a citation defect: every link resolves, every symbol exists, and every quoted substring is present, so no citation sweep can see it. The repair is contract prose in a `032` spec edit plus a `.py` docstring, and it belongs beside this card's spec-consistency-checker item, which is the gate that would have to read a quoted error message against the source literal. What turns on it: the spec is what a future change to that consumer-visible message would be checked against, and it currently tells a reader that removing `Meta.connection` is an offered remedy when the shipped message offers inheriting `relay.Node` instead.
```

Voice: matches the card's existing `scope` bullets — defect first, dated measurement, symbol paths per
[AGENTS.md][agents] rule 27 (never `path:NN`), why it is not the defect class a gate already catches,
and what turns on it. No process narration: no artifact, worker, slice, or cycle is named.

### Uniqueness check before the insert

```python
existing = list(CardItem.objects.filter(card=card, section=scope)
                .order_by("order").values_list("order", flat=True))
assert existing == list(range(0, 52))
assert not CardItem.objects.filter(card=card, section=scope, order=52).exists()
```

Both asserts passed: card 52's `scope` orders were a contiguous **0-51** (52 rows, no duplicates), so
**52 was the next free slot** against the `(card, section, order)` unique constraint. Confirmed landed:
the post-edit read shows pk 1409 at `card 52 | scope | order 52`.

---

## Item B — re-measuring the pk 1278 census

### Every figure re-derived, with its command

The bullet's shape check was **re-run over every companion**, not re-counted:

```shell
uv run python - <<'PY'
from pathlib import Path
appx = Path("docs/SPECS/appx")
H = ["## How to read this file", "## Provenance of this record", "## Entries keyed to the spec"]
for p in sorted(appx.glob("*-rationale.md")):
    lines = {l.strip() for l in p.read_text().splitlines()}
    print(len([h for h in H if h in lines]), p.name)
PY
```

| Figure in the bullet | Stale reading (2026-08-14) | Re-derived 2026-08-26 | Match? |
|---|---|---|---|
| `-rationale.md` companions in `docs/SPECS/appx/` | 13 | **36** | no |
| carry **all three** headings | 8 | **15** | no |
| carry **two** | (not stated) | **9** | new |
| carry **one** | 5 (the `0.0.14` cohort) | **12** | no |
| carry **none** | (not stated) | **0** | new |
| the all-three cohort is `spec-001…` through `spec-008…` | yes | **`spec-001` through `spec-015`**, still one contiguous run | no |
| the five `0.0.14` companions carry one or two of the three | yes | **yes** — `044`/`046` how-to-read only, `045` provenance only, `047`/`048` both | **yes, still holds** |
| spec-007 rationale bytes | 46,045 | **46,045** | yes |
| spec-007 spec bytes | 2,983 | **2,983** | yes |
| spec-007 ratio | 15.4x | **15.44x** | yes |
| next-highest ratio | 4.3x "of the thirteen pairs" | **10.29x** over 36 pairs (`spec-012-version_release_alignment-0_0_4`, 28,943 / 2,814) | **no — the population moved** |

Ratio table command:

```shell
uv run python - <<'PY'
from pathlib import Path
appx, specs = Path("docs/SPECS/appx"), Path("docs/SPECS")
rows = []
for p in sorted(appx.glob("*-rationale.md")):
    stem = p.name[: -len("-rationale.md")]
    s = specs / f"{stem}.md"
    rows.append((p.stat().st_size / s.stat().st_size, stem, p.stat().st_size, s.stat().st_size))
for r, stem, rb, sb in sorted(rows, reverse=True):
    print(f"{r:7.2f}x {stem} {rb} {sb}")
PY
```

All 36 companions have a spec pair (no orphan printed). Top of the table:

```text
  15.44x  spec-007-onboarding_docs_spec_consolidation-0_0_4  46045 /  2983
  10.29x  spec-012-version_release_alignment-0_0_4           28943 /  2814
   8.77x  spec-014-testing_shift-0_0_4                       76840 /  8760
   7.25x  spec-013-real_m2m_coverage-0_0_4                   41636 /  5739
   6.57x  spec-011-stale_placeholder_cleanup-0_0_4           22615 /  3440
   4.61x  spec-016-fieldmeta_consolidation-0_0_6             41926 /  9103
   4.28x  spec-002-optimizer-0_0_2                           41291 /  9647
```

**The old 4.3x figure was correct for its population, and re-deriving that is what proves the
population moved rather than the arithmetic.** The 2026-08-14 population is not stated in the bullet,
so it was reconstructed and then confirmed two independent ways: (i) the bullet names its own two
sub-cohorts — the eight `spec-001…008` all-three companions plus the five `0.0.14` companions — which
sums to exactly 13; (ii) restricted to that 13-member set the ratio table's next-highest after
spec-007 is `spec-002` at **4.28x ≈ 4.3x**, reproducing the figure exactly. A `git ls-tree` of
`docs/SPECS/appx/` at the surrounding commits brackets it (10 companions on 2026-08-10, 16 by
2026-08-15), consistent with 13 on 08-14.

Two further precision fixes the re-measurement forced: the bullet said "13 **files** in
`docs/SPECS/appx/`", but that directory also holds one `-terms.csv` per spec (90 files today, 36
rationale + 54 terms), so 13 was the rationale-companion count, not a directory count. And spec-031's
spec and companion are this cycle's own uncommitted work; spec-031 sits at 0.69x, far outside the top,
so it does not move the next-highest figure either way.

### The shape decays in two steps, and that is the new load-bearing fact

Per-heading totals over 36: `## Provenance of this record` **33**, `## Entries keyed to the spec`
**22**, `## How to read this file` **20**. By spec order:

| Run | Headings carried | Count |
|---|---|---|
| `spec-001` … `spec-015` | all three | 15 |
| `spec-016-fieldmeta_consolidation-0_0_6` | how-to-read + entries-keyed (no provenance) | 1 |
| `spec-017-deferred_scalars-0_0_6` … `spec-022-export_schema-0_0_7` | provenance + entries-keyed | 6 |
| `spec-023-multi_db-0_0_7` … `spec-031-globalid_encoding-0_0_9` | provenance only | 9 |
| `spec-044` … `spec-048` (the `0.0.14` five) | one or two | 5 |

### Is the decision overtaken by events? No

The bullet's open question — *whether the three-section shape becomes a documented template* — is
unchanged and is preserved verbatim in the rewrite, along with its named home (beside the
spec/rationale consistency checker this card already scopes). The re-measurement **sharpens** it rather
than answering it: on the 2026-08-14 reading the shape looked like an early-cycle habit that five
`0.0.14` companions had partially picked up; the 36-companion reading shows a monotone two-step decay
in spec order with a single break, and one heading (`## Provenance of this record`, 33 of 36) that has
become a convention in fact while the other two have not. That is a stronger case for deciding, not a
reason the decision no longer needs taking. The spec-007 sizing sub-question is likewise still live and
now better posed: spec-007 is no longer a lone outlier but the head of a tail of tiny-spec /
large-rationale pairs, all of them `0_0_4`-era.

### Before / after text of pk 1278

**Before** (1,313 bytes):

```text
The spec rationale companion file is on its eighth hand-reproduced instance: measured 2026-08-14, 8 of the 13 files in `docs/SPECS/appx/` carry all three of `## How to read this file`, `## Provenance of this record` and `## Entries keyed to the spec` - the companions to `spec-001-django_types-0_0_1` through `spec-008-definition_order_independence-0_0_4` - each rebuilding that shape by hand along with the deliberative-companion opener, `## Standing notes`, and the link-definition scaffold at `docs/SPECS/appx/` depth. The five `0.0.14` companions carry one or two of the three, which is itself part of the decision: the shape is either a template or a convention only the early cycles followed. Decide whether it becomes a documented template; the natural home is beside the spec/rationale consistency checker this card already scopes. Fold in one sizing question the spec-007 residual cycle raised: that pair measures 46,045 bytes of rationale against a 2,983-byte spec, a 15.4x ratio where the next-highest of the thirteen pairs is 4.3x, because every content claim the spec once made was falsified and each falsification is recorded with the commit that falsified it. Not a defect and not that cycle's to fix, but if the template lands it should say whether a companion that large owes an index or a split.
```

**After** (3,018 bytes):

```text
The spec rationale companion file is on its fifteenth hand-reproduced instance. Re-measured 2026-08-26 by re-running the three-section shape check over every companion rather than re-counting files: `docs/SPECS/appx/` holds 36 `-rationale.md` companions, and 15 of them carry all three of `## How to read this file`, `## Provenance of this record` and `## Entries keyed to the spec` - the companions to `spec-001-django_types-0_0_1` through `spec-015-relay_interfaces-0_0_5`, still one contiguous run - each rebuilding that shape by hand along with the deliberative-companion opener, `## Standing notes`, and the link-definition scaffold at `docs/SPECS/appx/` depth. Nine carry two of the three, twelve carry one, and none carries zero. This supersedes the 2026-08-14 reading of 8 of 13, whose all-three cohort ended at `spec-008-definition_order_independence-0_0_4`: that 13 was the rationale-companion population of the day (those eight plus the five `0.0.14` companions, not 13 files in the directory - `docs/SPECS/appx/` also holds a `-terms.csv` per spec), and it is 36 now because each residual cycle since has authored one. The wider population is not decay to nothing but decay in two steps, in spec order: `spec-001` through `spec-015` carry three; `spec-017-deferred_scalars-0_0_6` through `spec-022-export_schema-0_0_7` carry `## Provenance of this record` plus `## Entries keyed to the spec`; `spec-023-multi_db-0_0_7` through `spec-031-globalid_encoding-0_0_9` carry `## Provenance of this record` alone. `spec-016-fieldmeta_consolidation-0_0_6` is the single break in that order, carrying `## How to read this file` plus `## Entries keyed to the spec` and no provenance. `## Provenance of this record` now stands at 33 of 36 and is a convention in fact; the other two headings, at 20 and 22, are not. The five `0.0.14` companions still carry one or two of the three (`044` and `046` how-to-read only, `045` provenance only, `047` and `048` both of those), which is itself part of the decision: the shape is either a template or a convention only the early cycles followed. Decide whether it becomes a documented template; the natural home is beside the spec/rationale consistency checker this card already scopes. Fold in one sizing question the spec-007 residual cycle raised: that pair still measures 46,045 bytes of rationale against a 2,983-byte spec, a 15.4x ratio, but the comparison it was set against has moved. The next-highest of the thirteen pairs then was 4.3x (`spec-002-optimizer-0_0_2`); over the 36 pairs now it is 10.3x (`spec-012-version_release_alignment-0_0_4`, 28,943 bytes of rationale against a 2,814-byte spec), with `spec-014-testing_shift-0_0_4` at 8.8x and `spec-013-real_m2m_coverage-0_0_4` at 7.3x behind it. So spec-007 is no longer a lone outlier but the head of a small tiny-spec/large-rationale tail, every member of it `0_0_4`-era. Not a defect and not that cycle's to fix, but if the template lands it should say whether a companion that large owes an index or a split.
```

Editorial convention followed (the one pk 1243 records for its 08-15 / 08-25 / 08-26 readings): the
2026-08-14 reading is **named and superseded, with its figures quoted** (`8 of 13`, the cohort ending
at `spec-008…`, `4.3x` and its 13-pair population) rather than silently overwritten, so a later pass
cannot re-revert the rewrite by reading the old numbers as current. Untouched by design: the
`## Standing notes` / opener / link-scaffold clause, the "template or a convention only the early
cycles followed" framing, the open question and its named home, the spec-007 byte figures, and the
closing index-or-split sentence.

---

## How both writes were made

Via the ORM with a full `save()` / `create()` — never raw SQL, never `.update()` — so the `post_save`
side-row wiring in `examples/fakeshop/apps/kanban/signals.py` #"On first save of a linked model, create
its ``UUIDModel`` side-row" runs. The DB bootstrap installs the SQLite `busy_timeout` for the
maintainer's parallel sessions:

```python
import sys
sys.path.insert(0, "scripts")
from _kanban_lib import configure_django
configure_django()
from apps.kanban.models import Card, CardItem, Section
```

Both texts were asserted **ASCII-only** (`text.isascii()`) — matching card 52's existing `scope`
bullets, which use no non-ASCII character — and asserted to contain no `{{card_ref:N}}` placeholder, so
no `CardReference` row is created, retargeted, or orphaned.

One post-write correction: the new bullet first spelled the two ``or inherit `relay.Node` directly``
literals as single-backtick spans with backslash-escaped inner backticks. A single-backtick code span
cannot contain a backtick and a backslash does not escape inside one, so that would have rendered
broken in `KANBAN.md`. Both were rewritten as double-backtick spans (the `CardItem` pk 1374 precedent),
the DB re-saved, and both renders re-run.

---

## DB text-column sweep — is any OTHER row falsified?

Obligation: change only pk 1278 and add exactly one row, unless the sweep finds another row this
cycle's findings falsified. Every `TextField` / `CharField` on every model in the `kanban` app was
swept, enumerated from Django's model registry rather than a hand-written list — **53 columns across 28
models**:

```shell
uv run python - <<'PY'
import re, sys; sys.path.insert(0, "scripts")
from _kanban_lib import configure_django; configure_django()
from django.apps import apps as dj_apps
from django.db import models as m
rx = re.compile(r"How to read this file|Provenance of this record|Entries keyed to the spec|"
                r"hand-reproduced|remove the key|remediation|46,045|2,983|15\.4x|4\.3x|"
                r"three-section|documented template", re.IGNORECASE)
for model in dj_apps.get_app_config("kanban").get_models():
    fields = [f for f in model._meta.get_fields()
              if isinstance(f, (m.TextField, m.CharField)) and not f.auto_created]
    for obj in model.objects.all():
        for f in fields:
            if rx.search(getattr(obj, f.name) or ""):
                print(model.__name__, f.name, obj.pk)
PY
```

**8 hits, every one read.** Dispositions:

- `CardItem` pk 1278 and pk 1409 — this slice's own two rows.
- `Card.planning_note` pk 65 / 66 / 67 / 68 and `CardTransition.note` pk 4 — all five match only on the
  word "remediation" in the security-audit-program sense (`Security-audit remediation program, card N
  of 4`). Unrelated vocabulary collision. **No edit owed.**
- `CardItem` pk 1337 (card 52, `note` order 6) — discusses what `## How to read this file` should state
  inside `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`. Its subject is that one
  companion's content, not the census or any remediation tail; nothing in it is falsified by either
  finding. **No edit owed.**

**Result: no other row was falsified. Exactly one row changed and exactly one added, as scoped.**

---

## DB-level control: `iterdump()` diff against a read-only copy outside the repo

Read-only HEAD copy and a pre-edit copy of the working DB, both written **outside** the repository
(never `git stash` / `git checkout` — the maintainer runs concurrent sessions against this tree):

```shell
git show HEAD:examples/fakeshop/db.sqlite3 > <scratch>/db-head.sqlite3
cp examples/fakeshop/db.sqlite3            <scratch>/db-pre.sqlite3    # before any edit
# ... edits ...
cp examples/fakeshop/db.sqlite3            <scratch>/db-post.sqlite3
for n in head pre post; do sqlite3 "file:<scratch>/db-$n.sqlite3?mode=ro" .dump > <scratch>/dump-$n.sql; done
```

**Control 1 — HEAD vs the pre-edit working DB.** Exactly one changed line, Slice 7's pk 1243. This is
what proves the DB was dirty only with a known prior slice before this pass started:

```text
2808c2808
< INSERT INTO kanban_carditem VALUES(1243,...,'2026-08-25 20:20:24.049589','Decide whether a `-rationale.md` ...
---
> INSERT INTO kanban_carditem VALUES(1243,...,'2026-08-27 00:33:40.019286','Decide whether a `-rationale.md` ...
```

**Control 2 — the pre-edit working DB vs post-edit.** This slice's whole footprint:

```text
2843c2843
< INSERT INTO kanban_carditem VALUES(1278,...,'2026-08-15 00:18:14.274573','The spec rationale companion ...
---
> INSERT INTO kanban_carditem VALUES(1278,...,'2026-08-27 01:31:24.238570','The spec rationale companion ...
2973a2974
> INSERT INTO kanban_carditem VALUES(1409,'2026-08-27 01:31:24.241078','2026-08-27 01:33:31.119509','`docs/SPECS/spec-032-full_rel...
10274a10276
> INSERT INTO kanban_uuidmodel VALUES(...,'8421babe398d4862b1f12621b1cbadb7',NULL,1409,NULL,...);
10292c10294
< INSERT INTO sqlite_sequence VALUES('kanban_carditem',1408);
---
> INSERT INTO sqlite_sequence VALUES('kanban_carditem',1409);
```

**Exactly one changed row (pk 1278, its text plus its `modified` timestamp) and one added row (pk
1409).** The two remaining lines are the mechanical consequences of an insert, not extra edits: the
`sqlite_sequence` autoincrement counter, and the `kanban_uuidmodel` one-hot side row whose `carditem`
column holds `1409` — the `post_save` side row a raw SQL insert would have skipped, so its presence is
positive evidence the write went through the ORM. Slice 7 saw one changed line because it performed no
insert; this pass's expected shape is one changed plus one added, and that is what the dump shows. No
other table touched, no row deleted, no card renumbered or re-statused.

---

## Re-render verification

`scripts/build_kanban_html.py` was read before running it rather than assumed: `DATA_BLOCK_RE` matches
`<!-- KANBAN_DATA_START -->…<!-- KANBAN_DATA_END -->` and the writer is a single `DATA_BLOCK_RE.subn`
followed by `html_path.write_text` — the generator rewrites **only** that embedded data block and leaves
the hand-maintained Vue shell alone. Confirmed from source, not from memory.

```shell
uv run python scripts/build_kanban_md.py
# Wrote 70 cards (excluded 1 backlog cards) and 15 board docs to .../KANBAN.md   exit 0
uv run python scripts/build_kanban_html.py
# Wrote 71 cards, 15 board docs, and 11 lookup arrays to .../KANBAN.html         exit 0

uv run python scripts/build_kanban_md.py --check    # "KANBAN.md is up to date."   exit 0
uv run python scripts/build_kanban_html.py --check  # "KANBAN.html is up to date." exit 0
```

Both `--check` runs **exit 0**. Rendered diff against HEAD:

```shell
git diff --stat -- KANBAN.md KANBAN.html
#  KANBAN.html | 2 +-
#  KANBAN.md   | 5 +++--
```

`KANBAN.html`'s single changed line is the embedded JSON data block (one line by construction; the
`-U0` diff shows both `KANBAN_DATA` markers intact around it). `KANBAN.md`'s three touched lines are:
Slice 7's pk-1243 bullet (present at pass start, attributed by
`git diff -U0 -- KANBAN.md | grep '^+' | grep -c "Re-measured 2026-08-26 after the spec-031 residual
cycle"` → 1), this slice's rewritten pk-1278 bullet, and this slice's added pk-1409 bullet, which lands
as the last `#### Scope` bullet immediately after the order-51 entry. Both new bullets confirmed
present in the rendered file (`grep -c` → 1 each). The pre-edit `--check` was clean and the post-edit
`--check` is clean, so the renders moved exactly with the DB and nothing else.

---

## Final status

```text
 M KANBAN.html
 M KANBAN.md
 M django_strawberry_framework/types/definition.py
 M django_strawberry_framework/types/relay.py
 M docs/SPECS/spec-031-globalid_encoding-0_0_9.md
 M docs/SPECS/spec-032-full_relay-0_0_9.md
 M examples/fakeshop/db.sqlite3
?? 0_0_14.md
?? docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md
?? docs/builder/bld-031-final.md
?? docs/builder/bld-031-integration.md
?? docs/builder/bld-031-slice-0-rationale_extraction.md
?? docs/builder/bld-031-slice-1-meta_key_setting_precedence.md
?? docs/builder/bld-031-slice-2-encode_seam.md
?? docs/builder/bld-031-slice-3-decode_seam.md
?? docs/builder/bld-031-slice-4-live_http.md
?? docs/builder/bld-031-slice-5-docs_wrap.md
?? docs/builder/bld-031-slice-6-spec_032_citation_repair.md
?? docs/builder/bld-031-slice-7-card_052_companion_census.md
?? docs/builder/bld-031-slice-8-spec_032_spec_030_citations.md
?? docs/builder/bld-031-slice-9-card_052_homing.md
?? docs/builder/build-031-globalid_encoding-0_0_9.md
```

Paths this slice dirtied: `examples/fakeshop/db.sqlite3`, [KANBAN.md][kanban], [KANBAN.html][kanban-html],
and this artifact — and the first three were already `M` from Slice 7. Every other entry is this
cycle's earlier work or a concurrent session's. Nothing staged, nothing committed, no branch created or
switched. No `bld-031-*` artifact deleted.

### Not fixable inside the fence

- **The three `spec-032` / test sites themselves stay wrong.** Repairing
  `docs/SPECS/spec-032-full_relay-0_0_9.md` #"Re-affirmation coverage for the two already-shipped
  diagnostics", the same file's #"remediation (shipped; re-affirmed)" entry, and
  `tests/types/test_base.py::test_connection_key_requires_relay_node`'s docstring is explicitly out of
  this slice's scope and is a future `032` cycle's call. The board now carries the finding, which is
  the whole point of this slice; the `.py` docstring half will need whichever cycle owns it to touch a
  test file, so a `032` spec-only pass leaves a third of the defect standing.
- **`spec-032`'s Slice 1 tests are described as pinning "the documented messages"** while the spec's
  own documented message for that gate is false. A future repair should treat the assertion as the
  source of truth and the prose as the defect, in all three places, rather than the reverse.

### Summary

Homed the two findings that lived only in this cycle's scratchpads onto
`TODO-ALPHA-052-0.0.16`. Added `CardItem` pk 1409 (card 52, `scope`, order 52) recording that
`spec-032` attributes an "or remove the key" remediation to the `Meta.connection` Relay-Node gate in
**two** places while the shipped tail from
`django_strawberry_framework/types/base.py::_validate_connection` is ``or inherit `relay.Node`
directly.`` — a third site, `tests/types/test_base.py::test_connection_key_requires_relay_node`'s
docstring, was found by this pass and was not in the handed lead. Corrected `CardItem` pk 1278's census
by re-running the three-section shape check over all 36 companions rather than re-counting files: 15
carry all three (not 8 of 13), the all-three cohort now runs `spec-001` to `spec-015` (not to
`spec-008`), 9 carry two, 12 carry one, none carries zero, and the spec-007 next-highest comparison
moved from 4.3x over 13 pairs to 10.3x over 36. The "five `0.0.14` companions carry one or two"
claim and every spec-007 byte figure re-derived unchanged. A 53-column sweep across 28 kanban models
found no other falsified row; the `iterdump()` control shows exactly one changed row and one added row
plus an insert's two mechanical consequences; both renderers regenerated and `--check` exit 0.

### Spec changes made (Worker 1 only)

None. This slice edits no spec file. `docs/SPECS/spec-032-full_relay-0_0_9.md` was read-only; its
repair is recorded on the board and deferred to a future `032` cycle by maintainer scope.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md
[kanban]: ../../KANBAN.md
[kanban-html]: ../../KANBAN.html

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md

<!-- docs/builder/ -->

[build-031]: build-031-globalid_encoding-0_0_9.md
[build-md]: BUILD.md

<!-- django_strawberry_framework/ -->

[types-base]: ../../django_strawberry_framework/types/base.py

<!-- tests/ -->

[test-types-base]: ../../tests/types/test_base.py

<!-- examples/ -->

[fakeshop-db]: ../../examples/fakeshop/db.sqlite3

<!-- scripts/ -->

[build-kanban-html]: ../../scripts/build_kanban_html.py
[build-kanban-md]: ../../scripts/build_kanban_md.py

<!-- .venv/ -->

<!-- External -->
