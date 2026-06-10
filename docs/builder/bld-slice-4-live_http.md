# Build: Slice 4 — live HTTP coverage (model-label emitted IDs, the headline filter round-trip, the deterministic `type`-opt-out)

Spec reference: `docs/spec-031-globalid_encoding-0_0_9.md` (lines 101-104; Test plan ~612-621; Definition of done item 6 ~681; Risks "Deterministic `type`-opt-out setup" P3 and "Default-flip blast radius")
Status: final-accepted

## Plan (Worker 1)

This slice proves the shipped Slice-1/2/3 behavior **live** over the real
`/graphql/` HTTP stack. Slices 1-3 already shipped (all `final-accepted`):

- Slice 1 — the `Meta.globalid_strategy` key + `RELAY_GLOBALID_STRATEGY` setting +
  the precedence resolver.
- Slice 2 — the encode seam. **The package default is now `model`**, so every
  emitted `GlobalID` carries the Django model label (`app_label.modelname:<pk>`,
  e.g. `products.item:42`), not the GraphQL type name. The strategy-aware filter
  (Decision 13) accepts the model-label payload under the default `model` strategy
  and **rejects** the old `Type:<pk>` form.
- Slice 3 — the decode seam (`decode_global_id` + `registry.definition_for_graphql_name`),
  package-internal only.

Slice 4 ships exactly three things (spec lines 101-104 — no scope beyond them):

1. **Update existing live `GlobalID` assertions** in
   `examples/fakeshop/test_query/` for the model-label payload — both the
   **emitted-ID** assertions and the **filter-INPUT** assertions (the strategy-aware
   filter now rejects the old type-anchored inputs the suite builds).
2. **Add three live tests** (a/b/c): (a) an emitted `node { id }` decodes to the
   model-label payload; (b) the **`0.0.9` headline workflow** — feed the emitted
   model-label `GlobalID` straight back as `filter: { id: { exact: "<that id>" } }`
   and get the right row; (c) the `type`-strategy opt-out reproduces the
   GraphQL-type-name payload, set up **deterministically**.
3. **A deterministic `type`-opt-out fixture helper** (spec Risks P3): refactor the
   products schema-reload into a callable helper (the `library` suite already has
   this shape — `_reload_library_project_schema()` wrapped by an autouse fixture),
   then drive the opt-out test with a test-local
   `override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"})`
   + `registry.clear()` + reload **inside** the test (so the override is active
   BEFORE the reload finalizes the schema).

This slice touches ONLY `examples/fakeshop/test_query/` test files. No package
source. No standing-doc edits (see the TODAY.md reconciliation under
`### Spec changes made (Worker 1 only)`).

### Concrete model-label map (verified against the live schema)

The products / library / kanban Relay-Node types have **no `Meta.name`**, so each
type's `graphql_type_name` equals its class name, and `model._meta.label_lower`
is `app_label.modelname` keyed on the Django app **label** (last path segment):

| Type (class) | model | model-label payload (`label_lower`) | old type-name payload |
|---|---|---|---|
| `CategoryType` | `products.Category` | `products.category` | `CategoryType` |
| `ItemType` | `products.Item` | `products.item` | `ItemType` |
| `PropertyType` | `products.Property` | `products.property` | `PropertyType` |
| `EntryType` | `products.Entry` | `products.entry` | `EntryType` |
| `GenreType` | `library.Genre` | `library.genre` | `GenreType` |
| `BookType` | `library.Book` | `library.book` | `BookType` |
| `LoanType` | `library.Loan` | `library.loan` | `LoanType` |
| `CardType` | `kanban.Card` | `kanban.card` | `CardType` |

(`apps.kanban` `AppConfig.name = "apps.kanban"` → Django app **label** `kanban` →
`model._meta.label_lower == "kanban.card"`; mirrors how `apps.products` →
`products.category`. Worker 2 verifies each label at write-time — the durable way
is `models.Card._meta.label_lower`, not a hand-typed literal where the ORM object
is in scope; see Implementation discretion items.)

### DRY analysis

**Existing patterns reused (cite file:line — pin-at-write-time hints).**

- **The `_decode_global_id(global_id) -> (type_name, node_id)` test helper**
  (`test_library_api.py:672-681`): base64-decodes a `GlobalID` string and partitions
  on `":"`. REUSE this exact helper for the library emitted-ID assertions (the
  type-name slot just moves from `"GenreType"` to `"library.genre"` — same decode,
  new expectation). `test_products_api.py` has NO such helper today; its new
  emitted-ID test (a) should decode via `relay.GlobalID.from_id(id)` (already
  imported as `relay`) per the source-site TODO pseudocode at
  `test_products_api.py:104-105` (`relay.GlobalID.from_id(id).type_name == "products.item"`),
  rather than re-introducing a second base64 helper. ONE decode idiom per file; do
  not copy the library helper into products.
- **The `_global_id(type_name, pk)` helper** (`test_products_api.py:96-97`):
  builds a `GlobalID` string. REUSE it unchanged — the SIGNATURE stays
  `(type_name, pk)`; only the call-site `type_name` argument moves from
  `"ItemType"`/`"CategoryType"`/`"EntryType"` to the model labels
  `"products.item"`/`"products.category"`/`"products.entry"`. Do NOT rename the
  helper or change its body. (The same applies to the inline
  `relay.GlobalID(type_name="CategoryType", node_id=...)` builders in the filter
  tests — only the `type_name` literal moves.)
- **The library reload-as-callable-helper pattern**
  (`test_library_api.py:19-50`): `_reload_library_project_schema()` is a plain
  callable; the autouse `_reload_project_schema_for_acceptance_tests` fixture just
  calls it. This is the EXACT shape spec Risks P3 wants the products suite to adopt
  so the opt-out test can call the reload itself (inside an `override_settings`
  block). The products autouse fixture (`test_products_api.py:42-67`) currently
  inlines the reload body — Slice 4 extracts it into a callable named helper, and
  the autouse fixture calls it. The reload pattern is mandated by
  `examples/fakeshop/test_query/README.md` #"clear the global registry, reload
  ... then reload the project schema and URLconf" and `docs/TREE.md`.
- **The `override_settings(DJANGO_STRAWBERRY_FRAMEWORK={...})` precedent**: the
  Slice-2 callable-setting tests (`tests/types/test_relay_interfaces.py`) and the
  Slice-1 precedence test already drive `RELAY_GLOBALID_STRATEGY` through
  `override_settings` + a registry-clear + reload; `conf.settings` reads
  `DJANGO_STRAWBERRY_FRAMEWORK` from Django settings (`AGENTS.md` #"reads
  `DJANGO_STRAWBERRY_FRAMEWORK` from the consumer's settings dict"). `test_multi_db.py:52`
  already imports `override_settings` in this directory — the idiom is established
  here.
- **The `_post_graphql` / `_assert_graphql_data` HTTP helpers**
  (`test_products_api.py:70-85`, `test_library_api.py:76-89`): REUSE for all new
  tests; do not hand-roll a second `client.post("/graphql/", ...)`.
- **`seed_data(N)` / `create_users(N)`** (`apps.products.services`): the mandated
  first-line seeders (`AGENTS.md` #"First line of every catalog/auth test:
  seed_data(N)"). The new products tests seed via `seed_data(1)`; library tests
  use inline `Model.objects.create` (the library app has no `services.py` —
  `AGENTS.md` #"Library acceptance tests use inline Model.objects.create").

**New helpers justified (single responsibility each).**

- **One extracted callable: `_reload_products_project_schema()`** in
  `test_products_api.py` — single responsibility: clear the registry, reload
  `apps.products.schema` → `config.schema` → `config.urls`, clear URL caches. It is
  the verbatim body of the current autouse fixture, lifted out so the opt-out test
  (c) can invoke the reload itself **after** applying `override_settings`. The
  autouse fixture (`_reload_project_schema_for_acceptance_tests`) becomes a one-line
  wrapper calling it — byte-for-byte the library shape. No NEW reload logic; just a
  refactor-to-callable mirroring `test_library_api.py:19-50`. This is the ONLY new
  helper, and it exists solely to satisfy the spec's "not a brittle import-order
  exercise" requirement.

**Duplication risk avoided.**

- **Do NOT introduce a second products base64-decode helper.** Test (a) decodes the
  emitted products `id` via `relay.GlobalID.from_id(...)` (the source-site TODO's
  own pseudocode), not by copying `test_library_api.py::_decode_global_id`. The
  library file keeps its existing `_decode_global_id`; products uses the `relay`
  parse API it already imports. One decode idiom per file.
- **Do NOT re-type the model-label string as a literal where the ORM object is in
  scope.** Worker 2 may assert against `models.Item._meta.label_lower` /
  `f"{models.Genre._meta.label_lower}"` rather than a hardcoded `"products.item"`
  in the body of a test that already holds the model — this keeps the expectation
  derived from the same source the encoder reads (mirrors the suite's existing
  "compare API == ORM" data-driven posture, `test_products_api.py:18-22`). A
  hardcoded label string is acceptable in a docstring or where no model object is
  bound, but the load-bearing assertion should derive it. Discretion item.
- **Do NOT duplicate the opt-out reload.** The opt-out test (c) calls the SAME
  extracted `_reload_products_project_schema()` inside its `override_settings`
  block — it does not inline a third copy of the registry-clear/reload sequence.
- **The `_global_id(type_name, pk)` builder stays one helper.** Every products
  filter-input test that builds a `GlobalID` routes through `_global_id` or the
  existing inline `relay.GlobalID(...)`; the model-label move is purely a
  `type_name`-argument change, never a parallel new builder.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current
source before editing — the suite is CURRENTLY broken by the Slice-2 default flip
(that breakage is exactly this slice's job to fix; spec Risks "Default-flip blast
radius"). Re-verify the broken-test inventory against the live suite during the
build (`uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py
examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_kanban_api.py`
to see the current failures), per the spec's "re-run the affected suites at
implementation time" instruction (spec line 621).

#### A. `examples/fakeshop/test_query/test_products_api.py`

1. **Refactor the reload fixture into a callable helper (spec Risks P3).** Lift the
   body of the autouse `_reload_project_schema_for_acceptance_tests`
   (`test_products_api.py:42-67`) into a module-level callable
   `_reload_products_project_schema()` (mirror `test_library_api.py:19-50`:
   `registry.clear()` → reload/import `apps.products.schema` → `config.schema` →
   `config.urls` + `clear_url_caches()`). The autouse fixture becomes a one-line
   wrapper that calls it. Behavior-preserving for every existing test; enables test
   (c) to drive the reload under `override_settings`.

2. **Move the emitted-ID expectations to the model label.** In
   `test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`
   (`test_products_api.py:178-223`), the expected dict pins
   `_global_id("EntryType", entry.pk)` (line 183),
   `_global_id("ItemType", entry.item_id)` (line 186), and
   `_global_id("CategoryType", entry.item.category_id)` (line 189). Change the
   `type_name` argument of each to the model label: `"products.entry"`,
   `"products.item"`, `"products.category"` (or `models.Entry._meta.label_lower`
   etc. — discretion). The `_global_id` helper and the pk arguments are unchanged.

3. **Move the filter-INPUT GlobalIDs to the model label (Decision 13).** Three
   tests build a `CategoryType:<pk>` filter input that the `model`-strategy filter
   now rejects:
   - `test_products_categories_filter_by_relay_own_pk_global_id_in`
     (`test_products_api.py:285-302`): the `gids` comprehension builds
     `relay.GlobalID(type_name="CategoryType", node_id=...)` (line 296) → move
     `type_name` to `"products.category"`.
   - `test_products_items_filter_by_related_category_global_id`
     (`test_products_api.py:331-345`): `gid` at line 335 → `"products.category"`.
   - `test_products_items_filter_and_order_compose`
     (`test_products_api.py:455-476`): `gid` at line 465 → `"products.category"`.
   These are own-PK `GlobalIDMultipleChoiceFilter` (`id: { in: [...] }`) and the
   `Item.category` `RelatedFilter` traversal (`category: { id: { exact: ... } }`),
   so they prove the strategy-aware filter accepts the model-label payload through
   `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter` / `RelatedFilter` child filters.

4. **Add live test (a): `test_emitted_globalid_is_model_anchored`** (spec line
   616). `seed_data(1)`; query `allItems { id name }` over `/graphql/`; decode the
   first item's `id` via `relay.GlobalID.from_id(id)` and assert
   `.type_name == models.Item._meta.label_lower` (`"products.item"`) and
   `.node_id == str(item.pk)`. (Realizes the source-site TODO pseudocode at
   `test_products_api.py:100-112`; remove that TODO comment block in the same change
   since the work it anchors now lands.)

5. **Add live test (b): `test_globalid_filter_round_trip` — THE HEADLINE
   WORKFLOW** (spec line 617, DoD item 6). `seed_data(1)`; query `allItems { id name }`,
   capture the model-label `id` string the API just emitted for one specific item
   (do NOT reconstruct it — take the value the API returned, the strongest
   round-trip proof); feed it straight back as
   `allItems(filter: { id: { exact: "<that id>" } }) { id name }`; assert the
   response contains exactly that one item (by name/id). `ItemFilter.Meta.fields`
   is `{"id": "__all__", ...}` (`apps/products/filters.py:62`), so `id` carries the
   `exact` lookup the headline query needs. This proves the strategy-aware filter
   (Decision 13) accepts the very payload the encoder now emits — the `0.0.9`
   reason-for-being.

6. **Add live test (c): `test_type_strategy_opt_out_reproduces_type_name`** (spec
   line 618, Risks P3). Deterministic shape:
   - `seed_data(1)` (outside the override is fine; rows persist).
   - `with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"}):`
     call `_reload_products_project_schema()` **inside** the block so the schema
     finalizes WITH the `type` strategy active (the override must precede the reload
     — that is the whole point). Then query `allItems { id }` and assert the decoded
     `id`'s `type_name` is the GraphQL type name `"ItemType"` (==
     `ItemType.__name__`, since no `Meta.name`), NOT the model label.
   - **Restore cleanup:** after the `with` block (or via fixture teardown), the
     autouse fixture re-reloads the default-strategy schema for the next test;
     `override_settings` already restores settings on exit, and the autouse fixture
     runs per-test, so the next test's reload sees the default `model` strategy
     again. Worker 2 confirms the opt-out reload does not leak the `type` schema
     into a sibling test (the autouse fixture's per-test reload is the guard; if a
     belt-and-suspenders re-reload inside the test after the `with` block reads
     cleaner, that is discretion — but verify no leakage either way).

   Note the spec's named alternative (a dedicated opt-out type / root field whose
   IDs are intentionally type-anchored, e.g. uncommenting `globalid_strategy = "type"`
   on a fakeshop type per the `apps/products/schema.py:93-99` TODO). **Preferred is
   the `override_settings` + reload-helper path** — it neither churns unrelated
   expected IDs nor weakens the default-flip coverage (a permanently-flipped type
   would do both, per spec Risks P3). Pin the override-path; do not take the
   permanent-type-flip alternative unless the override path proves unworkable
   (escalate to the maintainer if so — do not silently switch approaches).

#### B. `examples/fakeshop/test_query/test_library_api.py`

7. **Move the emitted-ID round-trip expectation.** In
   `test_library_relay_node_global_id_round_trips` (`test_library_api.py:684-712`),
   `assert type_name == "GenreType"` (line 710) → `"library.genre"` (or
   `models.Genre._meta.label_lower`). The `_decode_global_id` helper
   (`test_library_api.py:672-681`) and the `node_id == str(genre.pk)` assertion
   (line 711) stay. Update the docstring/comment-level reference to the payload if
   it names `GenreType` as the wire payload.

8. **Move the connection-edge emitted-ID expectation.** Around
   `test_library_api.py:2165-2168`, the loop decodes `edge["node"]["id"]` and
   asserts `type_name == "GenreType"` → `"library.genre"`. (Re-verify the exact
   line at build-time; the Slice-2 notes flagged ~2167-2168.)

9. **Move the filter-INPUT GlobalIDs to the model label (Decision 13).**
   - `test_library_books_filter_by_relay_m2m_global_id` (`:893-`): `global_id` at
     line 904 builds `type_name="GenreType"` → `"library.genre"` (M2M
     `genres.id` GlobalID input).
   - `test_library_genres_filter_by_relay_own_pk_global_id_in_list` (`:918-`):
     `gid_sci_fi` / `gid_fantasy` at lines 934-935 build `type_name="GenreType"`
     → `"library.genre"` (own-PK `id: { in: [...] }`).
   - `test_library_genres_filter_by_relay_own_pk_global_id_in_rejects_wrong_type`
     (`:949-969`): the `wrong` input at line 956 builds `type_name="BookType"` — a
     **wrong-type** input that must STILL be rejected. The wrong-type form changes
     from `BookType:<pk>` to the model label `library.book` (so it stays a genuine
     wrong-model GlobalID under the `model` strategy — `library.book` is not
     `library.genre`); the `assert "GlobalID type mismatch" in ...message` (line
     969) stays. Re-verify the message still fires under the model strategy
     (Decision 13 keeps the wrong-model rejection for the three framework
     strategies).
   - `test_relay_global_id_filter_rejects_wrong_type_name` (`:1310-1335`):
     `right_id` (line 1318, `GenreType`) → `library.genre`; `wrong_id` (line 1319,
     `LoanType`) → `library.loan`; the `assert "GlobalID type mismatch" in message`
     (line 1334) stays. **Re-verify the mismatch-message TEXT assertion**: the
     Slice-2 filter now reports the model label in the mismatch message
     (`filter expects library.genre but received library.loan`), so any assertion
     that pins the SPECIFIC expected/received token (e.g. `"GenreType" in message`,
     Slice-2 notes flagged ~line 1335) must move to the model-label token
     (`"library.genre" in message`). A bare `"GlobalID type mismatch" in message`
     check needs no token change.

#### C. `examples/fakeshop/test_query/test_kanban_api.py`

10. **Move the filter-INPUT GlobalIDs to the model label (Decision 13).** In
    `test_filter_cards_by_own_pk_relay_global_id_in` (`test_kanban_api.py:262-`),
    `gid_filters` / `gid_conn` (lines 265-266) build
    `relay.GlobalID(type_name="CardType", node_id=...)` → `"kanban.card"` (==
    `models.Card._meta.label_lower`). Own-PK `id: { in: [...] }`. Verify there is no
    OTHER `CardType:<pk>` filter input or emitted-ID assertion in the file at
    build-time (grep `CardType`/`GlobalID` across the file).

#### D. Re-verify the inventory is complete

11. **Grep-sweep the whole `test_query/` tree** at build-time for any remaining
    `GlobalID(type_name="<TypeName>"` builders, `_global_id("<TypeName>"`,
    `type_name == "<TypeName>"`, or `"<TypeName>" in message` assertions that the
    Slice-2 inventory did not name (Slice-2 notes are a pin-at-write-time list, not
    a guarantee). The Slice-2 build report enumerated: `test_products_api.py`
    (3 filter-input + the depth-2 emitted-ID), `test_library_api.py`
    (emitted round-trip 710, connection edge ~2167-2168, filter inputs 904/934-935/956/1318-1319,
    mismatch-text ~1335), `test_kanban_api.py` (265-266). Confirm `test_scalars_*`,
    `test_glossary_api.py`, `test_multi_db.py` carry no Relay-Node `GlobalID`
    assertions that move (the scalars suite uses a non-Relay integer-PK filter per
    `test_scalars_filter_api.py:124`; `test_multi_db.py` reloads `library`/`BookType`
    — check whether it decodes/builds a `BookType` GlobalID and, if so, move it to
    `library.book`). Any newly-found site is in-scope Slice-4 churn (same
    Decision-13 / default-flip cause), not new scope.

### Test additions / updates

Per spec Test plan "Slice 4" (spec lines 612-621) and DoD item 6 (spec line 681).
All live HTTP via `django.test.Client` against `/graphql/`. Pinned assertion shapes:

**New tests (`test_products_api.py`):**

- `test_emitted_globalid_is_model_anchored` — `seed_data(1)`; `allItems { id name }`;
  `relay.GlobalID.from_id(id).type_name == "products.item"` (== `models.Item._meta.label_lower`)
  and `.node_id == str(item.pk)`.
- `test_globalid_filter_round_trip` (**headline**) — `seed_data(1)`; query
  `allItems { id name }`, capture the emitted model-label `id` for one item, feed it
  back as `allItems(filter: { id: { exact: "<that id>" } }) { id name }`, assert the
  response is exactly that one row. Use the API-EMITTED id string verbatim (not a
  reconstructed one) so the test proves true emit→filter symmetry.
- `test_type_strategy_opt_out_reproduces_type_name` — `seed_data(1)`; inside
  `with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"}):`
  call `_reload_products_project_schema()`, query `allItems { id }`, assert the
  decoded `type_name == "ItemType"` (the GraphQL type name, NOT `products.item`).
  Deterministic: the override is applied BEFORE the reload finalizes the schema.

**Updated assertion shapes (existing tests):**

- `test_products_api.py` emitted-ID: `_global_id("EntryType"/"ItemType"/"CategoryType", …)`
  → `_global_id("products.entry"/"products.item"/"products.category", …)`
  (lines 183/186/189).
- `test_products_api.py` filter-input: `type_name="CategoryType"` → `"products.category"`
  (lines 296, 335, 465).
- `test_library_api.py` emitted-ID: `assert type_name == "GenreType"` → `"library.genre"`
  (lines 710 and ~2167-2168).
- `test_library_api.py` filter-input: `type_name="GenreType"` → `"library.genre"`
  (904, 934-935, 1318); `type_name="BookType"` → `"library.book"` (956);
  `type_name="LoanType"` → `"library.loan"` (1319). Wrong-type rejections STILL
  raise `"GlobalID type mismatch"`; any specific-token mismatch-message assertion
  (`"GenreType" in message`, ~1335) → the model-label token (`"library.genre"`).
- `test_kanban_api.py` filter-input: `type_name="CardType"` → `"kanban.card"`
  (265-266).

**Fixture refactor (`test_products_api.py`):** extract
`_reload_products_project_schema()` callable; autouse fixture calls it. Mirrors
`test_library_api.py:19-50`. Behavior-preserving.

Temp/scratch tests: none required — every assertion is a live HTTP query against
the example schema. Worker 3 should confirm (a) the headline round-trip test (b)
uses the API-EMITTED id (not a reconstructed one); (b) the opt-out test (c) applies
`override_settings` BEFORE the reload (the determinism contract); and (c) the
opt-out `type` schema does not leak into a sibling test (the per-test autouse reload
is the guard).

### Implementation discretion items

Assessed and intentionally delegated to Worker 2 (equivalent-shape / data-source
choices); none are architectural escape hatches:

- **Deriving the expected model label from `Model._meta.label_lower` vs a hardcoded
  literal.** Preferred is deriving from the ORM object where one is in scope
  (matches the suite's data-driven API==ORM posture); a hardcoded `"products.item"`
  in a docstring or where no model is bound is acceptable. Worker 2's call per site,
  provided the load-bearing emitted-ID assertion in test (a) derives the label.
- **The products emitted-ID decode idiom for the new tests** — `relay.GlobalID.from_id(id)`
  (the source-site TODO's pseudocode, `relay` already imported) is preferred over
  copying `test_library_api.py::_decode_global_id`. Worker 2 picks the exact spelling
  (`.type_name` / `.node_id` attribute reads), but does NOT introduce a second
  base64 helper in the products file.
- **Whether the opt-out test (c) adds a belt-and-suspenders re-reload after the
  `with override_settings(...)` block** vs relying solely on the per-test autouse
  fixture to restore the default schema — either, provided no `type`-strategy schema
  leaks into a sibling test. Worker 2 verifies non-leakage by running the full
  products suite.
- **Exact test names** within the spec's named intents (a/b/c) — the spec's
  Test-plan names (`test_emitted_globalid_is_model_anchored` /
  `test_globalid_filter_round_trip` / `test_type_strategy_opt_out_reproduces_type_name`)
  are recommended; minor wording is Worker 2's call.
- **Which products type drives tests (a)/(b)/(c)** — `ItemType` is the spec's
  worked example (`products.item`), but `CategoryType` etc. are equally valid.
  `ItemType` recommended for consistency with the spec narrative.

No unresolved architectural questions — nothing escalated to the maintainer.

Static-inspection helper: **skipped** for this slice. The BUILD.md "must run"
triggers are package source under `types/` / `optimizer/` or files ≥150 source
lines of new logic; this slice touches only `examples/fakeshop/test_query/` test
files and adds one small reload-fixture refactor (no non-trivial logic). Skip
recorded here per BUILD.md "the skip must be recorded explicitly with a short
reason." (Worker 2/3 MAY run it on the fixture helper if it grows non-trivial
logic, but it is a verbatim lift of an existing reload body, so this is not
expected.)

### Spec slice checklist (verbatim)

The Slice-4 nested sub-bullets from the spec's `## Slice checklist` (spec lines
101-104), copied verbatim. **The `TODAY.md` filtering-example clause in the first
sub-bullet is reconciled to Slice 5** (see `### Spec changes made (Worker 1 only)`):
the spec edit annotated that clause as Slice-5-owned, so the verbatim text below
reflects the post-edit spec and the `TODAY.md` portion is NOT a Slice-4 contract.

- [x] Slice 4: live HTTP coverage on a Relay-Node-shaped fakeshop type (per the card DoD)
  - [x] Update the existing live `GlobalID` assertions in [`examples/fakeshop/test_query/`][fakeshop-test-products] (and [`test_library_api.py`][fakeshop-test-library]) for the new model-label payload — the default-flip changes every **emitted** `GlobalID`, so the response-shape assertions that pin `id` (the `_global_id("ItemType"/"CategoryType"/"EntryType", …)` expectations in [`test_products_api.py`][fakeshop-test-products] and the `assert type_name == "GenreType"` round-trip in [`test_library_api.py`][fakeshop-test-library]) move to `products.item:<pk>` / `library.genre:<pk>`. **The existing filter-input tests must ALSO move to the model-label form** — under the default `model` strategy the strategy-aware filter ([Decision 13](#decision-13--globalid-filter-validation-is-strategy-aware)) accepts `products.category:<pk>` and **rejects** the old `CategoryType:<pk>` input those tests build, so they are not unchanged (correcting the earlier rev's claim). (The [`TODAY.md`][today] own-PK `GlobalID` filtering-example correction is **owned by Slice 5** — see Slice 5 line below and the [Doc updates](#doc-updates) section — so Slice 4 stays purely the `examples/fakeshop/test_query/` suite plus any test fixture helper; the standing-doc edits, including the `TODAY.md` filtering examples, the breaking-wire-format note, and the `type+model`-first upgrade sequence, all land together in Slice 5 to avoid a double-edit of the same lines.)
  - [x] Add live tests: (a) an emitted `node { id }` decodes to the model-label payload (base64 of `"app_label.modelname:<pk>"`); (b) **the `0.0.9` headline workflow — a `filter: { id: { exact: "<emitted model-label GlobalID>" } }` round-trips to the right row through the real products API** (proving the strategy-aware filter accepts the model-label payload it now emits, [Decision 13](#decision-13--globalid-filter-validation-is-strategy-aware)); (c) the `type`-strategy opt-out reproduces the GraphQL-type-name payload, set up deterministically (see below).
  - [x] **Deterministic `type`-opt-out setup ([`docs/feedback.md`][feedback] P3).** The fakeshop acceptance fixtures reload schemas at import/finalization, so a `RELAY_GLOBALID_STRATEGY = "type"` override must be active *before* the reload or the test silently exercises the default schema; and permanently flipping an existing products type to `"type"` would churn unrelated expected IDs and weaken the default-flip coverage. Preferred shape: factor the products schema-reload into a callable fixture helper (the [`library`][fakeshop-test-library] suite already has one), then drive the opt-out test with a test-local `override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"})` + `registry.clear()` + reload inside the test. Alternative: a dedicated opt-out type / root field whose IDs are intentionally type-anchored. The implementation plan names this so Slice 4 is not a brittle import-order exercise.

### Spec changes made (Worker 1 only)

- **`docs/spec-031-globalid_encoding-0_0_9.md` line 102 (Slice 4 checklist, first
  sub-bullet) — TODAY.md ownership reconciliation.** Triggered by this slice
  (Slice 4 planning). The spec listed the `TODAY.md` own-PK `GlobalID`
  filtering-example edit under BOTH Slice 4 (line 102: "Update the `TODAY.md` own-PK
  `GlobalID` filtering examples to `products.item:<pk>` etc.") AND Slice 5 (line 109
  + the Doc-updates section ~632: the products `GlobalID`-filtering examples + the
  breaking-wire-format note + the `type+model`-first upgrade sequence). Touching
  `TODAY.md` in two slices risks a double-edit / merge churn and a silently-double-
  or-un-addressed checklist box. **Resolution (the spec's own recommended path):
  ALL standing-doc edits — including the `TODAY.md` filtering-example correction —
  stay in Slice 5**; Slice 4 stays purely `examples/fakeshop/test_query/` + the test
  fixture helper. I edited line 102 to replace the bare "Update the `TODAY.md` …"
  imperative with an annotation that the `TODAY.md` filtering-example correction is
  **owned by Slice 5** (citing the Slice 5 line and the Doc-updates section), so the
  Slice-4 verbatim checklist no longer carries a sub-check Slice 5 will satisfy.
  - **Evidence this is the right boundary:** the source-site TODO in `TODAY.md`
    itself is already anchored to **Slice 5** (`TODO(spec-031-globalid_encoding-0_0_9
    Slice 5)` at `TODAY.md:10`), and it already enumerates the exact edits — replace
    type-name payload examples with `products.item:<pk>`, describe the pre-1.0
    wire-format break, prescribe the `type+model`-first sequence. The codebase was
    already pinning `TODAY.md` to Slice 5; the spec's Slice-4 line 102 was the
    redundant one.
  - **No material scope change to Slice 5:** Slice 5's contract (line 109 +
    Doc-updates) already covers the same `TODAY.md` examples PLUS the breaking note;
    no checklist-wording change is needed there. **Flag for Worker 0:** the Slice-4
    build-plan checklist entry (`build-031-...md` line 49) does not enumerate
    TODAY.md, so no build-plan edit is required — but Worker 0 should be aware that
    Slice 4's scope is now unambiguously `examples/fakeshop/test_query/`-only and
    Slice 5 remains the sole TODAY.md editor.

### Notes carried for downstream

- The `examples/fakeshop/test_query/` suite is CURRENTLY red (Slice-2 default flip +
  Decision-13 filter). Fixing it IS Slice 4. Worker 2 should run the affected suites
  first to capture the live failure set, then re-green them, then add (a)/(b)/(c).
- The integration pass owns a routed Slice-2 regression
  (`tests/test_registry.py::test_audit_runs_once_per_build`, the shared
  `models_with_multiple_types()` walk) — **not Slice 4 scope**, just context so it is
  not mistaken for a Slice-4 break.

---

## Build report (Worker 2)

### Files touched

Only `examples/fakeshop/test_query/` test files (no package source, no standing
docs). Classified against `git status --short` after both ruff invocations.

- `examples/fakeshop/test_query/test_products_api.py` — (1) refactored the autouse
  reload fixture body into a module-level callable `_reload_products_project_schema()`
  (mirror of `test_library_api.py::_reload_library_project_schema`); the autouse
  `_reload_project_schema_for_acceptance_tests` is now a one-line wrapper that calls
  it. (2) Added `override_settings` to the `django.test` import. (3) Removed the
  Slice-4 source-site TODO comment block (the work it anchored now lands). (4) Moved
  the depth-2 emitted-ID expectations in
  `test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` from
  `_global_id("EntryType"/"ItemType"/"CategoryType", …)` to
  `_global_id(models.Entry/Item/Category._meta.label_lower, …)`. (5) Moved the three
  filter-input GlobalID builders (`type_name="CategoryType"`) to
  `type_name=models.Category._meta.label_lower`
  (`test_products_categories_filter_by_relay_own_pk_global_id_in`,
  `test_products_items_filter_by_related_category_global_id`,
  `test_products_items_filter_and_order_compose`). (6) Added the three new live tests
  (a/b/c) — see below.
- `examples/fakeshop/test_query/test_library_api.py` — (1) removed the Slice-4
  source-site TODO comment block (its emitted-ID library work lands in the two
  emitted-ID assertion moves below, parallel to the products TODO removal). (2) Moved
  the emitted-ID round-trip assertion in `test_library_relay_node_global_id_round_trips`
  from `type_name == "GenreType"` to `models.Genre._meta.label_lower`. (3) Moved the
  connection-edge emitted-ID assertion in `test_genre_connection_full_round_trip`
  (`type_name == "GenreType"`) to `models.Genre._meta.label_lower`. (4) Moved the
  filter-input GlobalIDs: m2m `genres.id` (`GenreType`→`library.genre`), own-PK
  `id: { in: [...] }` list (`GenreType`→`library.genre`), the wrong-type-in-list
  rejection (`BookType`→`library.book`, still a genuine wrong-model GlobalID under the
  `model` strategy). (5) `test_relay_global_id_filter_rejects_wrong_type_name`:
  `right_id` `GenreType`→`library.genre`, `wrong_id` `LoanType`→`library.loan`, and the
  specific-token mismatch-message assertions (`"GenreType"`/`"LoanType"` in message)
  moved to the model-label tokens (`models.Genre/Loan._meta.label_lower in message`).
  The `"GlobalID type mismatch" in message` check is unchanged.
- `examples/fakeshop/test_query/test_kanban_api.py` — moved the own-PK filter-input
  GlobalIDs in `test_filter_cards_by_own_pk_relay_global_id_in`
  (`gid_filters` / `gid_conn`, `type_name="CardType"`) to
  `type_name=models.Card._meta.label_lower` (`kanban.card`).

### Tests added or updated

**New tests (`test_products_api.py`), all live `/graphql/` HTTP via `django.test.Client`:**

- `test_emitted_globalid_is_model_anchored` (spec line 616) — `seed_data(1)`; query
  `allItems { id name }`; decode the emitted `id` via `relay.GlobalID.from_id` and
  assert `.type_name == models.Item._meta.label_lower` (`products.item`) and
  `.node_id == str(item.pk)`.
- `test_globalid_filter_round_trip` (**headline**, spec line 617 / DoD item 6) —
  `seed_data(1)`; query `allItems { id name }`, capture the model-label `id` the API
  emitted for one item, feed it back **verbatim** as
  `allItems(filter: { id: { exact: "<that id>" } }) { id name }`, assert the response
  is exactly that one row (asserting on both `id` and `name`). Uses the API-emitted id
  string, not a reconstructed one — true emit→filter symmetry.
- `test_type_strategy_opt_out_reproduces_type_name` (spec line 618, Risks P3) —
  `seed_data(1)`; inside
  `with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"}):`
  call `_reload_products_project_schema()` (override applied BEFORE the reload
  finalizes the schema — the determinism contract), query `allItems { id name }`, assert
  the decoded `type_name == "ItemType"` (the GraphQL type name == `ItemType.__name__`,
  no `Meta.name`), NOT the model label.

**Updated assertion shapes:** every existing emitted-ID + filter-input + mismatch-message
GlobalID assertion across the three suites moved to the model-label form (enumerated under
Files touched).

**Fixture refactor:** `_reload_products_project_schema()` extracted; autouse fixture calls
it. Behavior-preserving (mirrors `test_library_api.py:19-50`).

### Validation run

- `uv run ruff format .` — pass (2 files reformatted: the two test files I edited;
  ruff collapsed the trailing-comma layouts I wrote where they fit inline).
- `uv run ruff check --fix .` — pass (5 errors auto-fixed in the edited test files;
  0 remaining).
- `git status --short` after both ruff invocations: modified —
  `examples/fakeshop/test_query/test_{products,library,kanban}_api.py` (slice-intended,
  in `### Files touched`); `django_strawberry_framework/{filters/base.py,filters/inputs.py,registry.py,types/base.py,types/definition.py,types/finalizer.py,types/relay.py}`
  + `tests/{filters/test_base.py,test_registry.py,types/test_base.py,types/test_relay_interfaces.py}`
  (the cumulative Slice 1-3 accepted package diff — EXPECTED per the build plan, workers
  never commit, NOT reverted); `docs/spec-031-globalid_encoding-0_0_9.md` (Worker 1's
  Slice-4 spec reconciliation, line 102 — EXPECTED, NOT reverted); untracked
  `docs/builder/bld-slice-{1,2,3,4}-*.md` + `build-031-*.md` (build artifacts). **No
  unrelated tool churn** — my edits touched only the three `test_query/` files I intended;
  nothing to revert.
- Focused tests (artifact-required, `--no-cov`, no `--cov*`):
  - Pre-edit baseline: `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py
    examples/fakeshop/test_query/test_library_api.py examples/fakeshop/test_query/test_kanban_api.py`
    → **10 failed, 97 passed** (the Slice-2 default-flip + Decision-13 blast radius this
    slice fixes; the live mismatch error confirmed the model-label message format:
    `GlobalID type mismatch: filter expects kanban.card but received CardType at index 0`).
  - Post-edit: same command → **110 passed** (107 pre-existing minus the 10-now-green
    plus the 3 new tests; the suite is GREEN under the model-label flip).
  - Non-leakage check (opt-out `type` schema does not bleed into siblings): ran
    `test_type_strategy_opt_out_reproduces_type_name` FIRST, then the two model-anchored
    tests immediately after → 3 passed. The per-test autouse reload restores the default
    `model` schema; no belt-and-suspenders re-reload needed.

### Implementation notes

- **Model-label expectations derived from `Model._meta.label_lower`, not hardcoded
  literals** (discretion item). Every load-bearing emitted-ID / filter-input / mismatch
  assertion derives the label from the ORM object (`models.Item._meta.label_lower`,
  `models.Genre._meta.label_lower`, `models.Card._meta.label_lower`, etc.), matching the
  suite's data-driven API==ORM posture. Verified each label equals the plan's table
  (`products.item`, `library.genre`, `kanban.card`, …) by running
  `_meta.label_lower` against the live ORM before editing.
- **Products decode idiom: `relay.GlobalID.from_id(id)`** (the source-site TODO's own
  pseudocode; `relay` already imported), reading `.type_name` / `.node_id`. Did NOT copy
  `test_library_api.py::_decode_global_id` into products — one decode idiom per file. The
  library file keeps its existing base64 `_decode_global_id` helper.
- **`_global_id(type_name, pk)` builder kept unchanged** — only the `type_name` argument
  at the call sites moved to model labels; signature and body untouched, no parallel
  builder introduced.
- **Opt-out test (c) relies solely on the per-test autouse fixture for cleanup** (no
  in-test re-reload after the `with` block) — verified non-leakage by the explicit
  ordered run above and by the full-suite green. `override_settings` restores settings on
  exit and the autouse fixture re-reloads the default schema per test.
- **Headline round-trip (b) asserts on both `id` and `name`** — the expected dict pins the
  API-emitted `id` string verbatim plus the item `name`, so the test fails if the filter
  returns the wrong row OR re-emits a different id.
- **Both source-site Slice-4 TODO comment blocks removed** (products and library) since
  the work each anchored now lands; the products plan named the products removal explicitly,
  and the library block is the exact parallel for the library emitted-ID moves.

### Notes for Worker 3

- Static-inspection helper: skipped per the plan (only `examples/fakeshop/test_query/`
  test files; the one refactor is a verbatim lift of the existing reload body — no
  non-trivial logic). No shadow files used.
- The 11 non-`test_query/` modified files in `git status` are the cumulative Slice 1-3
  accepted package diff + Worker 1's spec reconciliation; they are EXPECTED (workers never
  commit) and out of Slice-4 scope — do not flag them as Slice-4 churn.
- The wrong-type-rejection tests still assert `"GlobalID type mismatch"` and now build
  genuine wrong-MODEL GlobalIDs under the `model` strategy (`library.book` vs
  `library.genre`; `library.loan` vs `library.genre`), so Decision-13's wrong-model
  rejection still fires.

### Notes for Worker 1 (spec reconciliation)

None. No spec gap, conflict, or unstated assumption surfaced. The slice implemented
exactly the Worker 1 plan; all model labels matched the plan's table when verified against
the live ORM. No package-source defect discovered.

---

## Review (Worker 3)

Reviewed the Slice-4 contribution only (`git diff -- examples/fakeshop/test_query/`):
`test_products_api.py` (+97 net), `test_library_api.py`, `test_kanban_api.py`. The
11 modified `django_strawberry_framework/` + `tests/` files and the 1-line
`docs/spec-031-...md` edit are the cumulative Slice 1-3 accepted package diff and
Worker 1's reconciliation — confirmed out-of-Slice-4-scope and not re-reviewed.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

No DRY defects. Every reuse the plan mandated landed verbatim:

- `_global_id(type_name, pk)` (`test_products_api.py:105-106`) — signature and body
  unchanged; only the call-site `type_name` argument moved to the model label. No
  parallel builder introduced.
- `_decode_global_id` (`test_library_api.py`) reused for the library emitted-ID and
  connection-edge assertions; only the expectation moved (`"GenreType"` →
  `models.Genre._meta.label_lower`). Products uses `relay.GlobalID.from_id(...)` (the
  source-site TODO's pseudocode, `relay` already imported) — no second base64 helper
  added to the products file. One decode idiom per file, as planned.
- `_reload_products_project_schema()` (`test_products_api.py:42-70`) is a structural
  mirror of `test_library_api.py::_reload_library_project_schema` (`:19-44`): same
  `registry.clear()` → reload `apps.<app>.schema` → reload `config.schema` → reload
  `config.urls` + `clear_url_caches()` sequence. The autouse fixture is a one-line
  wrapper. The opt-out test (c) calls the SAME extracted helper inside its
  `override_settings` block — no third inline copy of the reload sequence.
- `_post_graphql` / `_assert_graphql_data` reused for every new test; `seed_data(1)`
  is the first line of each new products test per `AGENTS.md`.
- Model-label expectations derive from `Model._meta.label_lower` (data-driven
  API==ORM posture) rather than hardcoded literals — single-sourced from the same
  ORM attribute the encoder reads.

The repeated string literals the static helper flags (14) are GraphQL query
fragments inherent to a live-HTTP suite, not extractable DRY defects.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty. Slice 4 makes no
change to `__all__` or the re-export list (it touches no package source at all),
consistent with the DoD's "no new public exports" posture.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. (CHANGELOG-edit permission is
granted only in Slice 5 per spec Doc-updates / DoD item 7; Slice 4 correctly does
not touch it.)

### Documentation / release sanity

Not applicable in the doc/release/KANBAN/archive sense; slice modified only live
test files (`examples/fakeshop/test_query/`), not docs/release/KANBAN/archive
surfaces. One-line note on the test-data-derived assertion values: the model-label
assertions derive from `Model._meta.label_lower` and were verified against the live
ORM — `products.item` / `products.category` / `products.entry` / `library.genre` /
`library.book` / `library.loan` / `kanban.card` all match the plan's table exactly
(`uv run python manage.py shell` ORM check). `TODAY.md`, `README.md`,
`CHANGELOG.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`
are all untouched (`git status --short` empty for each); the `TODAY.md` source-site
TODO is anchored to `Slice 5`, confirming Worker 1's reconciliation that Slice 4
touches no standing docs.

### Spec slice checklist (verbatim) walk

All three Plan boxes are `- [x]` and each contract genuinely landed in the diff:

- **Box 1 — update existing emitted-ID + filter-input + mismatch-message
  `GlobalID` assertions to the model-label form.** Verified complete via a
  whole-tree grep: zero remaining `type_name="<Capital>"` builders,
  `_global_id("<Capital>"`, or `type_name == "<Capital>"` assertions, and zero
  `"<Capital>Type" in message` assertions across `test_query/` — the ONLY remaining
  capitalized type-name assertion is `parsed.type_name == "ItemType"` in the opt-out
  test (c), which is intentional and correct (the `type` strategy reproduces the
  GraphQL type name). Products: depth-2 emitted-ID (`:251/254/257`), 3 filter inputs
  (`:361/404/536`). Library: emitted round-trip (`:698`), connection edge (`:2172`),
  filter inputs (m2m / own-PK list / wrong-type / right+wrong mismatch), and the
  mismatch-message TEXT assertion moved to the model-label token
  (`models.Genre/Loan._meta.label_lower in message`). Kanban: own-PK list
  (`:265-266`). The wrong-type rejections still build genuine wrong-MODEL GlobalIDs
  (`library.book`/`library.loan` vs `library.genre`) so Decision-13's wrong-model
  rejection still fires (confirmed by the suite passing). None silently left broken.
  The `TODAY.md` portion of the spec sub-bullet is Slice-5-owned per Worker 1's
  recorded reconciliation — not a Slice-4 contract.
- **Box 2 — add live tests (a)/(b)/(c).** All three landed.
  (a) `test_emitted_globalid_is_model_anchored` decodes the API-emitted `id` via
  `relay.GlobalID.from_id` and asserts `.type_name == models.Item._meta.label_lower`
  (base64 of `products.item:<pk>`) and `.node_id == str(item.pk)`.
  (b) `test_globalid_filter_round_trip` — verified it captures `emitted_id =
  emitted["id"]` (the API-EMITTED value) and feeds that exact string back into
  `filter: { id: { exact: "{emitted_id}" } }`, asserting the response is
  `[{"id": emitted_id, "name": target.name}]`. It does NOT reconstruct the id, so it
  genuinely proves emit↔filter symmetry (the `0.0.9` headline / DoD item 6).
  (c) `test_type_strategy_opt_out_reproduces_type_name` asserts the decoded
  `type_name == "ItemType"`.
- **Box 3 — deterministic `type`-opt-out setup.** Verified the
  `override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY":
  "type"})` block WRAPS the `_reload_products_project_schema()` call (override active
  BEFORE the reload finalizes the schema), with the query + assertions inside the
  `with` block. The products reload is factored into the shared callable helper, and
  the per-test autouse fixture re-reloads the default `model` schema for siblings.
  Non-leakage is sound: `override_settings` restores settings on `with`-exit, and the
  autouse fixture's per-test reload (default strategy) runs before every sibling. The
  full-suite green (110 passed, any-order collection) corroborates no `type`-schema
  leakage. The `docs/TREE.md` reload pattern (clear registry → reload app schema →
  reload project schema + URLconf) is preserved in both the helper and its mirror.

### What looks solid

- The headline round-trip uses the API-emitted id verbatim (not a hand-built one)
  and asserts on both `id` and `name`, so it fails if the filter returns the wrong
  row OR re-emits a different id — the strongest possible emit→filter symmetry proof.
- Deterministic opt-out: the override precedes the reload; this is exactly the
  spec Risks P3 contract and avoids the silent-default-schema trap.
- The reload-to-callable refactor is behavior-preserving and byte-for-byte the
  library shape; the opt-out test reuses it rather than inlining a third copy.
- Model labels derived from `_meta.label_lower`, not hardcoded — keeps the
  expectation single-sourced from the same attribute the encoder reads.
- Both source-site Slice-4 TODO comment blocks (products + library) were removed in
  the same change that lands their anchored work, per `AGENTS.md`'s staged-TODO rule.
- Slice scope is clean: only `examples/fakeshop/test_query/`, no package source, no
  standing docs.

### Static helper

Ran `uv run python scripts/review_inspect.py
examples/fakeshop/test_query/test_products_api.py --output-dir docs/shadow` (the
file crossed the ≥50-new-lines-outside-`django_strawberry_framework/` trigger).
Overview: 26 symbols, 1 control-flow hotspot
(`test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`, 45 lines /
1 branch — a long expected-dict literal, not complex logic; pre-existing, only its
emitted-ID literals moved), 0 TODOs (both source-site TODO blocks correctly
removed), 9 Django/ORM markers (all `_meta.label_lower` derivations or pre-existing
`select_related` queries — no package-logic surface). No review-worthy package
logic; live-test assertions + a verbatim-lifted reload helper only. The other two
files are below the threshold (kanban +8, library +54 net but all assertion-literal
moves, no new logic) and were reviewed by reading the diff directly.

### Temp test verification

None created. Every Slice-4 behavior is a live HTTP query against the example
schema; the focused suite run below is sufficient verification.

### Suite verification

`uv run pytest examples/fakeshop/test_query/test_products_api.py
examples/fakeshop/test_query/test_library_api.py
examples/fakeshop/test_query/test_kanban_api.py --no-cov` → **110 passed in 29.16s**.
Matches Worker 2's reported post-edit count (107 pre-existing − 10 now-green + 3 new
tests). GREEN. No `--cov*` flag used. (The routed Slice-2
`test_audit_runs_once_per_build` regression is integration-pass scope, not run here.)

### Notes for Worker 1 (spec reconciliation)

None. No spec ambiguity, possible spec edit, or follow-up slice candidate surfaced
in Slice 4. Worker 1's existing line-102 `TODAY.md` reconciliation is consistent
with the `TODAY.md` source-site TODO (anchored to Slice 5) and needs no further
action.

### Review outcome

`review-accepted`. All three verbatim spec-slice checklist boxes addressed in the
diff; zero High/Medium/Low findings; no DRY defects; public surface unchanged;
the `test_query/` suite is GREEN (110 passed); the headline round-trip genuinely
uses the API-emitted id; the opt-out override precedes the reload.

---

## Final verification (Worker 1)

Audited the cumulative S1-S4 working tree, scoped to the Slice-4 contract
(`git diff -- examples/fakeshop/test_query/`: `test_products_api.py` +122,
`test_library_api.py` +54, `test_kanban_api.py` +8). The 11 modified
`django_strawberry_framework/` + `tests/` files and the 1-line `docs/spec-031-…md`
edit are the accepted Slice 1-3 package diff and my own Slice-4 line-102
reconciliation — out of Slice-4 scope, not re-audited here.

**Spec slice checklist audit (the three Plan boxes, all `- [x]`).** Each contract
genuinely landed in the diff; no over-tick, no silent un-tick, no remaining `- [ ]`:

- **Box 1 — move existing emitted-ID + filter-input + mismatch-message `GlobalID`
  assertions to the model-label form.** LANDED. Verified by whole-tree grep: the
  only remaining capitalized type-name assertion across `test_query/` is
  `parsed.type_name == "ItemType"` in the opt-out test (c) — intentional and correct
  (the `type` strategy reproduces the GraphQL type name). Products: depth-2 emitted-ID
  (`_global_id(models.Entry/Item/Category._meta.label_lower, …)`), 3 filter inputs
  (`type_name=models.Category._meta.label_lower`). Library: emitted round-trip + the
  connection edge (`models.Genre._meta.label_lower`), m2m / own-PK-list / wrong-type-in-list
  (`library.book` — still a genuine wrong-MODEL GlobalID, so Decision-13's wrong-model
  rejection still fires) / right+wrong (`library.genre` / `library.loan`), and the
  mismatch-message TOKEN assertion moved to `models.Genre/Loan._meta.label_lower in message`
  (the bare `"GlobalID type mismatch" in message` check unchanged). Kanban: own-PK list
  (`models.Card._meta.label_lower`). **The `TODAY.md` clause in this sub-bullet is
  Slice-5-owned** (my line-102 reconciliation) — correctly annotated in the spec and NOT
  a silently-dropped Slice-4 obligation. Confirmed: the `TODAY.md` source-site TODO is
  anchored to `Slice 5` (`TODAY.md:10`), and Slice 5's checklist (spec line 109) + the
  Doc-updates section already own the same `TODAY.md` edit — no Slice-4 obligation lost.
- **Box 2 — add live tests (a)/(b)/(c).** LANDED. (a) `test_emitted_globalid_is_model_anchored`
  decodes the API-emitted `id` via `relay.GlobalID.from_id` and asserts
  `.type_name == models.Item._meta.label_lower` + `.node_id == str(item.pk)`.
  (b) `test_globalid_filter_round_trip` (headline) — see the genuine-symmetry confirmation
  below. (c) `test_type_strategy_opt_out_reproduces_type_name` asserts the decoded
  `type_name == "ItemType"`.
- **Box 3 — deterministic `type`-opt-out setup.** LANDED. The
  `override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"})`
  block WRAPS the `_reload_products_project_schema()` call (override active BEFORE the
  reload finalizes the schema), query + assertions inside the `with` block. The products
  reload is factored into the shared callable helper; the per-test autouse fixture
  re-reloads the default `model` schema for siblings. The preferred override path was
  taken — the alternative permanent-type-flip (`apps/products/schema.py:99`
  `globalid_strategy = "type"`) stays commented out, as planned.

**Headline round-trip is genuine (emit↔filter symmetry).** Read
`test_globalid_filter_round_trip` directly: it captures `emitted_id = emitted["id"]`
(the value the API returned), feeds that exact string back as
`filter: { id: { exact: "{emitted_id}" } }`, and asserts the response is
`[{"id": emitted_id, "name": target.name}]`. It uses the **API-emitted** model-label
GlobalID verbatim — it does NOT reconstruct one — so it genuinely proves the
strategy-aware filter (Decision 13) accepts the very payload the encoder now emits.
The dual `id` + `name` assertion fails if the filter returns the wrong row OR re-emits
a different id. This is the strongest emit→filter symmetry proof.

**DRY check across Slices 1-4.** Clean.
- `_reload_products_project_schema()` is defined ONCE (`test_products_api.py:42`);
  `registry.clear()` appears exactly once in the file (line 54, inside that one helper);
  the autouse fixture (line 76) and the opt-out test (line 172) both CALL it — no
  copy-pasted reload sequence. It is a structural mirror of
  `test_library_api.py::_reload_library_project_schema` (the shared cross-slice pattern).
- `_global_id(type_name, pk)` is defined once (`test_products_api.py:105`); signature
  and body unchanged; only the call-site `type_name` argument moved to model labels — no
  parallel builder.
- Products uses `relay.GlobalID.from_id(...)` for decode (the source-site TODO's own
  pseudocode); library keeps its base64 `_decode_global_id`. One decode idiom per file —
  no second base64 helper introduced into products.
- Model-label expectations derive from `Model._meta.label_lower` (single-sourced from the
  same attribute the encoder reads), not hardcoded literals.

**Existing tests still pass (focused, Slice-4 scope).**
`uv run pytest examples/fakeshop/test_query/test_products_api.py
examples/fakeshop/test_query/test_library_api.py
examples/fakeshop/test_query/test_kanban_api.py --no-cov` → **110 passed in 27.88s**.
GREEN. Explicit `--no-cov` (required — `pytest.ini` auto-applies `--cov`); no `--cov*`
flag used; full repo suite NOT run. Count matches the build/review reports
(107 pre-existing − 10 now-green + 3 new). The known Slice-2
`test_audit_runs_once_per_build` regression is integration-pass scope (the shared
`models_with_multiple_types()` walk), NOT Slice-4 scope, and is not in this focused set.

**Spec reconciliation.** No further Worker-1 spec edit needed. The only Slice-4 spec
edit (line 102 TODAY.md → Slice 5) already landed during the planning pass and is
re-stated under `### Spec changes made (Worker 1 only)` below. The spec status/header
lines (line 5) are the intentional contract record — the `## Slice checklist` "stays
unticked as the contract record (build progress is tracked in the build plan, not here)"
per spec line 5 — so per-spawn header re-verification is a no-op for this build; the
header is not stale. The Test plan (spec ~612-621) and DoD item 6 (~681) are satisfied
verbatim, test names included.

**Final status: `final-accepted`.**

### Summary

Slice 4 lands the live `/graphql/` HTTP coverage that proves the `0.0.9` model-anchored
GlobalID default end-to-end. It moves every emitted-ID, filter-input, and
mismatch-message `GlobalID` assertion across the products / library / kanban live suites
from the type-anchored form (`CategoryType:<pk>`) to the Django model label
(`products.category:<pk>`, derived from `Model._meta.label_lower`); adds three live tests
— (a) an emitted `node { id }` decodes to the model label, (b) the headline workflow
feeding an API-emitted model-label GlobalID straight back through
`filter: { id: { exact: … } }` to prove the strategy-aware filter (Decision 13) accepts
the payload it now emits, and (c) a deterministic `type`-strategy opt-out via
`override_settings` applied before a reload — and extracts the products schema reload into
a shared callable helper (mirroring the library suite) so the opt-out test can drive the
reload after the override. Touches only `examples/fakeshop/test_query/`; no package source,
no standing docs. Focused suite GREEN (110 passed).

### Spec changes made (Worker 1 only)

- **`docs/spec-031-globalid_encoding-0_0_9.md` line 102 (Slice 4 checklist, first
  sub-bullet) — TODAY.md ownership reconciliation** (made during the Slice-4 planning
  pass; re-stated here for this slice's final-verification record). Triggered by Slice 4.
  The spec previously listed the `TODAY.md` own-PK `GlobalID` filtering-example edit under
  BOTH Slice 4 (line 102) and Slice 5 (line 109 + the Doc-updates section). Editing
  `TODAY.md` in two slices risks a double-edit and a silently double- or un-addressed
  checklist box. **Resolution (the spec's own recommended path): all standing-doc edits,
  including the `TODAY.md` filtering-example correction, stay in Slice 5;** Slice 4 stays
  purely `examples/fakeshop/test_query/` + the test fixture helper. Line 102 was edited to
  annotate the `TODAY.md` clause as Slice-5-owned (citing the Slice 5 line and the
  Doc-updates section), so the Slice-4 verbatim checklist no longer carries a sub-check
  Slice 5 will satisfy. Evidence: the source-site TODO in `TODAY.md` itself
  (`TODO(spec-031-globalid_encoding-0_0_9 Slice 5)` at `TODAY.md:10`) was already anchored
  to Slice 5. No material scope change to Slice 5 (its contract already covers the same
  edit); no build-plan edit required (the Slice-4 build-plan entry never enumerated
  TODAY.md). No further spec edit was made during this final-verification pass.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[today]: ../../TODAY.md

<!-- docs/ -->
[feedback]: ../feedback.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-test-library]: ../../examples/fakeshop/test_query/test_library_api.py
[fakeshop-test-products]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
