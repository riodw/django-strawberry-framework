# spec-034 Permissions — Implementation vs. the django-graphene-filters cookbook recipes

Comparison pass. Subject: how the shipped spec-034 implementation lines up against
the two upstream cookbook reference files the package cribs from —
`~/projects/django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py`
(the consumer `get_queryset` cascade recipe) and `.../recipes/fields.py` (the
per-field `FieldSet` recipe). Read alongside the cookbook's `recipes/models.py`
(FK nullability) and its permission tests (`recipes/tests/test_permissions_nested.py`)
to pin upstream's *intended* behavior, not just its source shape.

No `pytest` run this pass (`AGENTS.md`: only when explicitly asked). This is a
source + upstream-test comparison; where a runtime claim is load-bearing it is
called out as such and tied to the upstream test that proves it.

**How to read this.** Each finding carries a `fix:` tag — `SPEC` (spec-doc edit),
`PRODUCTS DOC COMMENTS` (comment/marker refresh in the fakeshop app), or `none`
(verified-correct / forward note). Actionable findings (H1, L3) end with an
**Apply** block: an exact `path::Symbol` anchor and a before → after for a new dev
to land the change with no further discovery. Every code/spec claim below is
anchored in the `AGENTS.md` symbol-qualified form (`path::Symbol #"substring"`).

**Verdict.** The cascade *helper* is a faithful port of the cookbook's row-exclusion
mechanism, with package-specific tightenings already recorded in the spec. The
current product hooks deliberately diverge from the cookbook's consumer recipe in
one place: the cookbook keeps the `view_<model>` branch as a bare per-model grant
and resolves hidden FK targets with **sentinels**; our package never adopted that
sentinel resolver tier (Decision 6), so the Revision-8 fix made the branch
**cascade** instead. That is defensible and the runtime behavior is already
documented (Slice 4 checklist, Revision 8, the test plan) — the one remaining gap
is that **Decision 6 and the parity table** never name the cookbook divergence
explicitly, so "required parity" reads broader than it is. `fields.py` has no
`0.0.10` counterpart by design (deferred to `0.1.1`).

## Findings

### H1 — `view_<model>` semantics diverge from the cookbook (row-narrowing chosen over sentinels), but Decision 6 / the parity table don't say so — MEDIUM-HIGH — fix: SPEC

The cookbook's four `get_queryset` hooks
(`recipes/schema.py::ObjectNode.get_queryset` and siblings) use a three-branch
shape: staff → all; `has_perm("recipes.view_<model>")` → `queryset.filter(is_private=False)`;
else → `apply_cascade_permissions(cls, queryset.filter(is_private=False), info)`.
The **middle (`view_<model>`) branch does not cascade** — it is a bare per-model
grant. Our shipped hooks
(`examples/fakeshop/apps/products/schema.py::ItemType.get_queryset` and the three
siblings) now run `apply_cascade_permissions(...)` in **every** non-staff branch,
including `view_<model>` — verifiable inline: `ItemType.get_queryset`'s
`has_perm("products.view_item")` arm and its fallback arm both return
`#"apply_cascade_permissions(cls, queryset.filter(is_private=False), info)"`.

This is not a port slip — the cookbook's bare-filter `view_<model>` is
*deliberate*, and it is paired with a behavior our package never ported:

- Upstream regular/anonymous users **are** cascade-narrowed
  (`test_permissions_nested.py::test_non_staff_sees_public_objects` asserts the
  result equals `cascade_public_count` — public Objects whose ObjectType is also
  public). Our anonymous/`else` branch matches this exactly.
- Upstream `view_<model>` users are **not** cascade-narrowed and instead see all
  public rows of that model, with hidden non-null FK targets resolved as
  **sentinels** — real FK id preserved, other fields masked, `is_redacted=True`,
  *no error, no dropped row*. This is a first-class upstream mechanism, not a test
  artifact: `django_graphene_filters/object_type.py::AdvancedDjangoObjectType.get_node`
  catches the "row exists but `get_queryset` hid it" case and returns
  `_make_sentinel(pk=0)` instead of `None`/raising, and
  `AdvancedDjangoObjectType.__init_subclass_with_meta__` documents that **forward
  FK fields resolve *through* `get_node`** when the Relay `Node` interface is
  present (so the sentinel covers nested FK traversal, not just root `node(id:)`
  refetch). Proven live by
  `test_permissions_nested.py::test_view_object_user_object_type_id_consistency`
  (selects nested `objectType { … }`, asserts `assertResponseNoErrors`).

The cookbook's models confirm the structural parity that makes this matter:
`Object.object_type`, `Attribute.object_type`, `Value.attribute`, and
`Value.object` are all **non-null** FKs — identical to fakeshop's
`Item.category` / `Property.category` / `Entry.item` / `Entry.property`. So both
projects face the same question — *what does a `view_<model>` user see when a
visible row's mandatory FK target is hidden?* — and answer it differently:

| | cookbook (graphene stack) | spec-034 (strawberry stack) |
| --- | --- | --- |
| regular / anon branch | cascade (row exclusion) | cascade (row exclusion) — **parity** |
| `view_<model>` branch | bare filter; **row kept**, hidden FK → **sentinel** | **cascade**; row **dropped** |
| `view_<model>` + hidden non-null FK selected | resolves (sentinel), no error | row never returned (cascaded out) |

**The row-drop itself is NOT unique to us — it is the shared
`apply_cascade_permissions` helper, and the cookbook drops identically wherever it
invokes it** (its anon/regular branch; a cookbook consumer could put cascade in the
`view_<model>` branch too). Upstream is explicit that cascade and sentinel are the
two complementary tools for the same situation: `object_type.py::get_node`'s log
line reads *"… Use apply_cascade_permissions() in get_queryset to exclude parent
rows whose FK targets are hidden,"* and the class docstring's `.. warning::` says
to reach for cascade *"if [the sentinel redaction] is unacceptable for your use
case."* So our cascade-everywhere policy is an upstream-**sanctioned**
configuration — not an invented behavior.

What we genuinely lack is the **other** tool. The package consciously declined the
sentinel half: spec
`docs/spec-034-permissions-0_0_10.md::Decision 6 #"row exclusion is the cascade contract"`
ports only the cascade helper and leaves the resolver-level `get_node` sentinel out
of scope — and our forward-FK resolver reads the FK by a bare accessor with no
sentinel/`DoesNotExist` fallback:
`django_strawberry_framework/types/resolvers.py::_make_relation_resolver`'s nested
`forward_resolver` ends `#"return getattr(root, field_name)"` (contrast its
`reverse_one_to_one_resolver` sibling, which *does* wrap the accessor in
`#"except related_does_not_exist:"` → `return None`). So a bare-filter
`view_<model>` branch in our stack would raise `RelatedObjectDoesNotExist`
("Entry has no item") where the cookbook degrades to a sentinel. The H1 fix
(cascade in the `view_<model>` branch) is therefore the package's **only available
substitute** for the sentinel: we drop the row because we cannot mask the FK.

Net: the cascade **helper** is at parity (the "required parity" row holds — the
drop behaves identically in both stacks). The divergence is two-layered: (1) we
have **no sentinel `get_node` path** at all, so a consumer *cannot* reproduce the
cookbook's bare-filter `view_<model>` recipe in our package without hitting a hard
error (a real capability gap, broader than fakeshop); and (2) consequently our
example's `view_<model>` semantics are strictly **more restrictive** than the
cookbook's (relation-coherent narrowing vs. a per-model grant with sentinel FKs).
Both are reasonable given (1) — but the spec's `Decision 6` and parity table
present this next to a bare "required parity" claim without naming the divergence.

**Already documented (do not re-document):** the *runtime* cascade-everywhere
behavior is covered — `docs/spec-034-permissions-0_0_10.md` Slice 4 checklist
(`#"every non-staff branch — including the matching view_<model> permission"`),
the Revision 8 ledger entry (`#"the view_<model> branch cascades too"`), and the
test plan (`test_cascade_view_item_user_respects_category_visibility` /
`test_cascade_view_entry_user_nested_selection_drops_hidden_targets`). What is
*missing* is only the cookbook-divergence framing at Decision 6 + the parity table.

#### Apply (spec only — the code behavior is the defensible choice)

Two edits, both in `docs/spec-034-permissions-0_0_10.md`. No code change.

**1. Parity-table status cell** — `#"required parity"` row (the
`django_graphene_filters: permissions.py::apply_cascade_permissions` row). Qualify
the bare claim:

```diff
- | django_graphene_filters: permissions.py::apply_cascade_permissions … | permissions.py::apply_cascade_permissions (Decision 5) | **this card (`0.0.10`) — required parity** |
+ | django_graphene_filters: permissions.py::apply_cascade_permissions … | permissions.py::apply_cascade_permissions (Decision 5) | **this card (`0.0.10`) — required parity (helper-level; the consumer `view_<model>` branch intentionally diverges — see Decision 6)** |
```

**2. Decision 6** — append one note paragraph after the "Alternatives considered"
line. It names the divergence and fixes the "required parity" reading:

```markdown
**Consumer-recipe divergence (cookbook `view_<model>`).** Parity is at the *helper*
level. The cookbook's consumer recipe (`recipes/schema.py`) keeps its middle
`has_perm("recipes.view_<model>")` branch as a bare `queryset.filter(is_private=False)`
and leans on its resolver-level sentinel
(`object_type.py::AdvancedDjangoObjectType.get_node` / `_make_sentinel`,
`is_redacted=True`) to mask a hidden non-null FK target without dropping the row.
This package deliberately did not port that sentinel tier — `types/resolvers.py`'s
forward-FK `forward_resolver` reads the FK by bare `getattr(root, field_name)` with
no `DoesNotExist`/sentinel fallback — so the fakeshop hooks instead **cascade in
every non-staff branch, including `view_<model>`** (`apps/products/schema.py`,
Revision 8). Consequence: a `products.view_item` grant does **not** let a user see
an item whose `category` is hidden (the row drops), where upstream `view_object`
would keep the row and sentinel the FK. This is a taxonomy-consistent choice, not a
parity break — relation visibility is handled by row-narrowing
(`TODO-BETA-046-0.1.1` codifies FieldSet as the field-level tier; there is no
node-sentinel tier). The sentinel is a **deliberate non-goal**, not a deferral.
```

(Optionally add the same one-liner to the Slice 4 hook narrative, but it is already
implied by the checklist line — the Decision 6 note is the load-bearing one.)

### M1 — `fields.py` (the `FieldSet` per-field layer) has no `0.0.10` counterpart by design; the deferral boundary is clean — MEDIUM — fix: none (confirm + forward notes)

`recipes/fields.py` is entirely the **per-field** permission layer:
`*FieldSet(AdvancedFieldSet)` classes with `resolve_<field>` tiered visibility (a
shared `_resolve_date` giving staff → full / `view_<model>` → day / authenticated
→ month / anonymous → year precision), `check_<field>_permission` gates that
`raise GraphQLError` for anonymous, a computed `display_name`, and a `_user(info)`
helper. spec-034
`docs/spec-034-permissions-0_0_10.md::Decision 2 #"the per-field read gate is defined here and implemented with FieldSet"`
explicitly scopes this out: per-field read gates are hosted on `FieldSet`, a
`0.1.1` deliverable — the live card is **`TODO-BETA-046-0.1.1`** (`KANBAN.md`),
whose body already names the "redaction-vs-denial split" and `recipes/fields.py` as
its canonical shape. Our products types carry staged `fields_class` markers, but
the markers cite the **stale** number `TODO-BETA-038-0.1.1` — covered by L3. So
there is correctly nothing to port here for `0.0.10`.

Forward notes for the `0.1.1` port (not actionable now, recorded so they aren't
rediscovered cold):
- `fields.py` reads the user via `info.context.user` / `_user(info)`. The `0.1.1`
  port needs the same `info.context.request.user` adaptation our `get_queryset`
  hooks already make (`docs/spec-034-permissions-0_0_10.md::User-facing API #"info.context.request.user, not info.context.user"`).
  Centralizing a canonical `_user(info)` over
  `django_strawberry_framework/utils/permissions.py::request_from_info` would fix
  all `FieldSet` sites at once.
- `fields.py`'s `check_<field>_permission` gates are the same vocabulary as the
  shipped `FilterSet` / `OrderSet` `check_<field>_permission` gates that
  `Decision 11 #"existing check_<field>_permission filter/order gates survive unchanged"`
  already reconciles — the `FieldSet` read gate is that gate on a third host. No
  new contract, just a new host.
- Cookbook `ValueNode` **omits** `description` from `fields` ("not included for
  permissions testing"); our `EntryType.Meta` **keeps** `description` (line tagged
  `#"TODO-BETA-038-0.1.1 FieldSet read gates"` — stale number, see L3) so it can be
  FieldSet-gated later. Opposite tactic, same intent — ours defers rather than
  omits; fine, just note the two examples will read differently to a migrant.

### L1 — Query root shape: cookbook exposes single-node `Node.Field` entry points + connections; ours is connections-only — LOW — fix: none (deferred, documented)

`recipes/schema.py::Query` declares both `object_type = Node.Field(ObjectTypeNode)`
(single-node refetch) **and** `all_object_types = AdvancedDjangoFilterConnectionField(...)`
per type. Our `apps/products/schema.py::Query` is connections-only
(`all_categories` / `all_items` / `all_properties` / `all_entries`); the root
`node(id:)` / `nodes(ids:)` Relay entry points are deferred to the fakeshop-schema
activation card — live number **`TODO-BETA-052-0.1.5`** (the `Query` docstring
cites the stale `TODO-BETA-051-0.1.5` — see L3). Expected divergence-with-deferral;
no cascade implication (node refetch routes through the same `get_queryset`).

### L2 — Meta-key staging and `fields` spelling — LOW — fix: none (faithful incremental port)

Cookbook nodes carry `aggregate_class`, `fields_class`, and `search_fields`
**live** and use `fields = "__all__"`. Ours wires `filterset_class` /
`orderset_class` live (matching), stages the other three commented with their
card tags, and uses explicit field tuples instead of `"__all__"`. This is the
package's deliberate incremental-activation pattern (uncomment each as its card
ships) plus a more explicit field surface — not a gap. The stale staged-card
numbers on those commented lines are the subject of L3.

### L3 — Stale staged-card numbers in the products schema point readers at dead card ids — LOW — fix: PRODUCTS DOC COMMENTS

`examples/fakeshop/apps/products/schema.py` still stages future Meta keys against
**renumbered** card ids. (Note: this is *separate* from the `TODO-ALPHA-027/034`
permission comments Revision 8 already retargeted — those are fixed; these
`TODO-BETA-*` staging numbers are not.) Verified against `KANBAN.md`:

| Stale id in schema.py | Live KANBAN id | Card |
| --- | --- | --- |
| `TODO-BETA-038-0.1.1` | `TODO-BETA-046-0.1.1` | `FieldSet` |
| `TODO-BETA-039-0.1.2` | `TODO-BETA-047-0.1.2` | `Meta.search_fields` support |
| `TODO-BETA-040-0.1.3` | `TODO-BETA-049-0.1.3` | Aggregation subsystem |
| `TODO-BETA-051-0.1.5` | `TODO-BETA-052-0.1.5` | Fakeshop schema activation |

(`TODO-BETA-051` is especially wrong: the only live `051` card is `0.1.4`, a
different card — there is no `051-0.1.5`.)

This does not affect spec-034 behavior, but a migrant currently follows dead ids.
Refresh only the comments/docstring markers; **do not** hand-edit generated
`KANBAN.md` output.

#### Apply (comment/marker refresh only)

In `examples/fakeshop/apps/products/schema.py`, replace the stale ids everywhere
they appear (find-and-replace is safe — these strings occur only in comments and
one `Meta.fields` inline comment):

```
TODO-BETA-038-0.1.1  →  TODO-BETA-046-0.1.1   # 5 sites: module docstring + import + 4 fields_class lines + the EntryType "description" inline comment
TODO-BETA-039-0.1.2  →  TODO-BETA-047-0.1.2   # 5 sites: module docstring + 4 search_fields lines
TODO-BETA-040-0.1.3  →  TODO-BETA-049-0.1.3   # 6 sites: module docstring + import + 4 aggregate_class lines
TODO-BETA-051-0.1.5  →  TODO-BETA-052-0.1.5   # 1 site: the Query docstring "Still deferred to …" line
```

Anchors to spot-check after the sweep:
`schema.py #"DONE-034-0.0.10` permissions, `TODO-BETA-046-0.1.1` fieldsets"` (the
module-docstring roadmap line), `EntryType.Meta #"Future: drop this entry"` (the
`description` field comment), and `Query #"Still deferred to"` (the docstring).
After editing, run the repo's `uv run ruff format .` / `uv run ruff check --fix .`
per `AGENTS.md` (comment-only changes, but keep the habit).

## Verified faithful (no action)

- **Cookbook branch vocabulary** — staff, per-model view permission, and fallback
  users are still the three policy tiers. The fallback cascade branch is a 1:1
  port; the per-model view branch is the intentional H1 divergence and should not
  be described as faithful 1:1 behavior.
- **The cascade call shape** —
  `apply_cascade_permissions(cls, queryset.filter(is_private=False), info)`
  (`schema.py::ItemType.get_queryset` et al.) is byte-for-byte the cookbook's
  consumer line.
- **Context adaptation** — cookbook `getattr(info.context, "user", None)` →
  ours `getattr(getattr(info.context, "request", None), "user", None)`, required
  because `StrawberryDjangoContext` exposes `request`/`response`, not `.user`
  (`docs/spec-034-permissions-0_0_10.md::User-facing API #"info.context.request.user"`);
  correct and necessary, not a divergence.
- **Anonymous/regular cascade behavior** matches the cookbook's
  `test_non_staff_sees_public_objects` / `test_not_authenticated_cascade_permissions`
  (rows narrowed to public-with-visible-FK-targets at every depth).
- **The cascade helper itself** remains at contract parity with
  `django_graphene_filters/permissions.py::apply_cascade_permissions` (ported
  verbatim plus the Django-6.0 `column`-value correction in
  `django_strawberry_framework/permissions.py::_is_cascadable_edge #"getattr(field, \"column\", None) is not None"`;
  see spec Revisions 5/7).

## Relationship to the prior reviews

- The earlier `docs/feedback.md` pass (H1 non-null-FK runtime error, M1
  async-recourse text, M2 malformed-`fields=` `TypeError`) is **already resolved**
  in spec Revision 8 and the current code (every non-staff branch cascades; the
  sync-misuse text is surface-aware; `_validate_fields` rejects
  non-iterable/non-string `fields=` as `ConfigurationError`).
- `docs/feedback2.md` (the second post-build review) overlaps this pass at one
  point only: its **L1** swept the stale `TODO-ALPHA-027/034` *permission* comments
  (retargeted in Revision 8). The `TODO-BETA-*` *staging* numbers in **L3 above are
  a different, still-open set** — do both as one comment sweep if convenient.
- This pass does not re-open resolved items — it re-frames the H1 fix through the
  cookbook lens: the fix is sound, but it is a *divergence* from the reference
  recipe (which solves the same problem with sentinels), and H1's Apply block is
  what records that at Decision 6 + the parity table.

## Scope & card placement (alpha vs beta) — what defers, what's now

Phase rule (maintainer-stated): **alpha = match graphene-django + strawberry-django;
beta = the django-graphene-filters–specific surface.** `KANBAN.md` confirms it —
alpha cards `035–044` are mutations/uploads/forms/serializers/auth/channels/debug
(the two base libraries' parity), beta cards `045–057` are the
django-graphene-filters `Advanced*` surface (FieldSet, search, aggregation, …).

The package's own **redaction taxonomy** decides most of this.
`KANBAN.md::TODO-BETA-046-0.1.1` (`FieldSet`, "Why it matters") states it outright:
*"Filter / order / cascade all use queryset narrowing — they remove rows. FieldSet
is the one place where a row stays visible but a field is either redacted or guarded
behind an error."* So the package has two deliberate tiers — **relation/row
visibility = narrowing (cascade)**; **field visibility = FieldSet (redact value /
deny)** — and **no node-sentinel tier**. The upstream `get_node` sentinel is the
*third* approach the package consciously did not adopt (Decision 6 = row-exclusion).

Mapping each finding to where it belongs:

| Finding | Belongs to | Already carded? | Act now? |
| --- | --- | --- | --- |
| Relation-level **sentinel / `get_node` redaction** (`is_redacted`, `_make_sentinel`) — the H1 divergence | **beta** parity-adjacent; but **superseded by the row-narrowing tier** the package already chose | **No card — and arguably shouldn't get one.** 034 raised it as an open question and Decision 6 picked row-exclusion; `TODO-BETA-046-0.1.1` codifies FieldSet as the field-level redaction tier, not a node-sentinel tier | **No code.** Record as a **deliberate non-goal** (H1 Apply, edit 2), *or* a beta parity card only if strict django-graphene-filters parity is wanted — note it conflicts with the taxonomy |
| **FieldSet** per-field redaction/denial (`fields.py`) | beta | **Yes — `TODO-BETA-046-0.1.1`** (field-level only; does *not* cover node sentinels) | No (deferred) |
| Single-node `node(id:)`/`nodes` root fields | beta | **Yes — `TODO-BETA-052-0.1.5`** | No (deferred) |
| `search_fields` / `aggregate_class` staging | beta | **Yes — `TODO-BETA-047-0.1.2` / `TODO-BETA-049-0.1.3`** | No (deferred) |
| `view_<model>` cascade-everywhere semantics (H1 symptom) | alpha example choice | n/a | **Docs only** (H1 Apply) |
| Stale staged-card numbers (L3) | alpha hygiene | n/a | **Comment refresh** (L3 Apply) |

**Are we pigeonholed? No.** The H1 cascade-everywhere is not a stopgap for a missing
feature; it is the package *applying its own row-narrowing tier consistently*. A
future sentinel, if ever wanted, is still additive (a branch near
`django_strawberry_framework/types/resolvers.py::_make_relation_resolver #"return getattr(root, field_name)"`
plus the Relay node path); 034 locked nothing. So there is no structural reason to
build it now, and a real architectural reason not to: it competes with the
row-narrowing model the package committed to.

**Now-work is documentation only**, and is fully captured by the two Apply blocks
above:
1. H1 Apply — Decision 6 note + parity-table qualifier (the cookbook divergence /
   sentinel-as-non-goal framing).
2. L3 Apply — refresh the stale `TODO-BETA-038/039/040/051` staging numbers in
   `apps/products/schema.py` to `046/047/049/052`.

(`KANBAN.md` is DB-generated — any *card* change goes through the ORM + the KANBAN
exporters, not a hand-edit of `KANBAN.md`. The L3 sweep touches only source
comments, not the board.)

## Net

The implementation is a faithful port of the cookbook's cascade recipe; the
`Advanced*` surface (`fields.py` et al.) is correctly **beta** and already carded.
The relation-level sentinel has **no card** — but reading `TODO-BETA-046-0.1.1`
shows that's by design, not omission: the package's redaction taxonomy is
row-narrowing for relations + FieldSet for fields, with **no node-sentinel tier**.
So the H1 divergence is a *deliberate, coherent* choice; the right move is to
**document it as such** (H1 Apply → Decision 6) and refresh the stale staged-card
numbers (L3 Apply). We are **not** pigeonholed; nothing structural needs to happen
now, and no production code change is recommended.
