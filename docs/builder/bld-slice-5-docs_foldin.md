# Build: Slice 5 — S12 transport slice: migration note, deployment guidance, doc fold-in

Spec reference: `docs/spec-046-transport_security-0_0_15.md` (lines 256-341; supporting
Decisions 8 / 12 / 14 / 15 / 16 / 17 / 18 / 19, and `## Doc updates` at lines 2700-2768)
Status: final-accepted

## Plan (Worker 1)

### Pass preamble — spec status line, and corrections to the dispatch findings

**Spec status-line re-verification (mandatory per `worker-1.md`).** `docs/spec-046-…md:37-47`
reads `Status: **IN BUILD — Slices 1-4 (S1, S2, S9, S11) are built … Slice 5 remains.**`
That is accurate at the start of this pass. **No spec edit made** — the spec and its
rationale companion are frozen for this planning pass by the build plan's
`## Ownership partition`.

Four of Worker 0's pre-verified findings were re-verified here and hold. **Three were
wrong or incomplete, and the plan below is built on the corrected facts.** Worker 2 must
work from this section, not from any earlier prose.

**Confirmed — already satisfied on disk, VERIFY-ONLY (do not rewrite, never revert):**

| sub-check fragment | evidence |
|---|---|
| `auth/sessions.py::classify_transport` unrecognized-scope-type message | `git diff` shows the new text: `"Serve GraphQL over HTTP through DjangoGraphQLView in your URLconf, and over WebSocket through DjangoGraphQLProtocolRouter, so the scope carries a recognized protocol type."` Satisfies the bullet. |
| `auth/mutations.py::_login_resolve_body` / `::_logout_resolve_body` docstrings | both now say `an async Channels consumer` and add `Since spec-046 the package router serves no HTTP at all…`. Satisfies the bullet. |
| `conf.py` `MAX_REQUEST_BODY_BYTES` comment multipart carve-out | present at `conf.py #"EXCEPT for a multipart request"`, and it also already carries the Decision-8 co-requirement sentence. Satisfies the bullet. |
| `tests/test_views.py` mixin-privacy trivially-true assertion dropped | `tests/test_views.py::test_the_body_boundary_mixin_stays_private_and_sits_first_in_both_base_lists` now carries three assertions, none about `__all__`, and its docstring records why. Satisfies the Slice-2-prose fragment. |
| `test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce` docstring | the `"the spec's Edge-case sentence predicting a 413 is inaccurate"` clause is gone; the `400` explanation remains. Satisfies the Slice-2-prose fragment. |
| `test_transport_api.py` module docstring **first line** | already `"""Live ``/graphql/`` transport-boundary acceptance tests (spec-046 Slices 1-3).` — **and it is already that way at `HEAD`** (`git show HEAD:examples/fakeshop/test_query/test_transport_api.py \| head -1`). The Slice-3-prose sub-check is satisfied. See `### Notes for Worker 1` — the spec sentence asserting it "still scopes the file to `(spec-046 Slices 1-2)`" is itself falsified. |

**CORRECTION 1 — `docs/TREE.md` is missing FOUR rows, not two-and-a-half.**
`utils/sessions.py` has **no** row. `docs/TREE.md:214` and `:324` are `auth/sessions.py`
(inside the `auth/` block, after `mutations.py` / `queries.py`), not `utils/sessions.py`;
the `utils/` blocks at `:280-293` (current layout) and the target-layout equivalent list
13 modules and `sessions.py` is not among them. `views.py`, `_request_body.py` and
`consumers.py` likewise have no package-tree row (`docs/TREE.md:75` is
**graphene_django**'s `views.py`). `tests/test_views.py` has no test-tree row.
`uv run python scripts/build_tree_md.py --check` currently reports
`docs/TREE.md is not up to date` — that failure is Slice 5's work, not drift.

**CORRECTION 2 — `TODAY.md` is NOT the maintainer's concurrent work. It is this slice's
own unfinished work.** `git diff -- TODAY.md` is exactly two hunks: the
`**Channels ASGI router**` capability bullet at `:384` rewritten to the post-Slice-1
shape, plus one added link def `[readme-docs]: docs/README.md`. Nothing else in the file
is touched. That is precisely the "`README.md` / `TODAY.md` transport wording" obligation
of the spec's own Slice-5 sub-check. The same is true of `README.md` (one hunk, the
`## Status` paragraph). Ruling in `### Ruling 1` below.

**CORRECTION 3 — seven NET-NEW glossary terms ARE required; the "insertion dance" is
not skippable.** Worker 0's finding is correct only about the CSV: all 37 anchors in
`docs/spec-046-transport_security-0_0_15-terms.csv` exist as `GlossaryTerm` rows, and the
CSV holds no new-symbol anchor. But the spec's `## Doc updates` GLOSSARY bullet
(`:2738-2741`) additionally requires **"the new terms this card authors (the package
Django view, the body cap, the UTF-8 wire contract, the consumer-injection seam, the
revalidation window, the connection-scoped revocation contract, and the WebSocket Host
boundary)"**, and `grep '^## ' docs/GLOSSARY.md` finds **none** of them — the only
transport-ish headings are `## \`DjangoGraphQLProtocolRouter\`` and
`## Channels request adapter`. So Slice 5 authors seven new `GlossaryTerm` rows.
Measured DB facts for the insertion: `GlossaryTerm.objects.count() == 119`;
`Meta.ordering = ["entry_order", "title_sort"]`; `entry_order` is a dense sequence
starting at `5`, `index_order` a dense sequence starting at `1`; statuses are
`shipped` / `planned` only; there are 15 `GlossaryCategory` rows and the router sits in
`integration-tooling`. Mechanism ruled in `### Ruling 3`.

**Other measured baseline facts (re-verified, so Worker 2 does not re-derive them):**

- Card `65` is `status=wip`, milestone `Alpha (pre-0.1.0)`, target version `0.0.15 (alpha)`.
- Its `SpecDoc` exists **and its `url` is already correct**:
  `https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-046-transport_security-0_0_15.md`.
  Worker 0's step 1 is therefore **verify-only**, not an update. (Worker 0's claim that
  `.save()` "sets `milestone_id`" is also not a thing: the milestone is already set and
  never changes; `DONE-046-0.0.15` is a *rendering* rule that drops the milestone prefix
  for done cards — compare `DONE-045-0.0.14`, whose milestone is still `Alpha (pre-0.1.0)`.)
- `card.glossary_links.count() == 0` — so the bootstrap link is genuinely required before
  the flip, per `apps/kanban/signals.py` `DONE_CARD_GLOSSARY_ERROR`.
- `TrackedPath.objects.filter(cards=card_65).count() == 0`. So the card flip has **no**
  effect on `docs/TREE.md`'s target-layout section, and there is no flip-before-TREE
  ordering constraint. (`scripts/build_tree_md.py` also skips any planned `TrackedPath`
  whose path already exists on disk, independent of card status.)
- `apps/kanban/signals.py` `STATUS_TRANSITIONS` allows `("wip", "done")`.
- `_STRAWBERRY_CHANNELS_BROKEN_HINT` in `routers.py` already reads
  `strawberry-graphql>=0.316.0` (Slice 4's fix landed), which is what makes six of
  `spec-041`'s eleven `0.262.0` mentions factually wrong about live code.
- `routers.py` composes `DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(...))))`
  (`routers.py:458-461`), and `websocket_consumer_class` + a positive
  `websocket_revalidation_window` **is** a construction error (`routers.py:437-438`).
- `consumers.py` closes a revoked connection with `_REVOCATION_CLOSE_CODE = 4403` /
  `_REVOCATION_CLOSE_REASON = "Forbidden"` (`consumers.py:197-198`), gating
  `next` / `data` / operation-scoped `error` only.
- All four package modules and both test modules have a period-terminated docstring first
  line, so the `build_tree_md.py` render will not reject one.

### Slice-level declarations

- **Floor-verification scope: `none`.** Per `BUILD.md` `## Floor verification`
  `### When it is required`, this slice touches no Django / Strawberry / channels
  integration seam. Its only `.py` edits are a class-docstring re-word in `views.py` and
  a docstring first line in `tests/test_views.py` — no executable change, no import-time
  change, nothing version-sensitive. Everything else is Markdown, the glossary/kanban DB,
  and four render scripts in `scripts/` (outside the coverage gate and outside the
  package). Worker 2 writes
  `Not applicable; plan declares floor-verification scope none.` in
  `### Floor verification`. **No floor venv is built for this slice, and the shared
  `.venv` is never mutated.** The canonical floor (Django 5.2.0 / Python 3.10 /
  strawberry-graphql 0.316.0 / channels 4.3.2) is stated in `BUILD.md`
  `## Floor verification`; this artifact does not restate it as a fact of any environment.
- **Hot-path declaration: `none`.** No code path changes. A module/class docstring is
  evaluated once at import, never per request, per resolver, per row, per connection, or
  per outbound message. Worker 2 writes
  `Not applicable; plan declares no hot path.` in `### Hot-path budget`.
  This is a **slice-level** declaration and deliberately does not touch the build-wide
  **M5** escalation in the build plan's `## Open maintainer decisions` (the WS-revocation
  lock-through-send number), which stays open and pending a maintainer decision. Worker 2
  must not re-litigate M5 or M4.
- **New boundary count: `0`.** No guard, cap, rejection path, or validation branch is
  added or changed. `### Failability proofs` is therefore
  `None; this pass introduced no new boundary.` — that literal, with the heading kept.
- **Split question, answered in writing (`BUILD.md` `### Slice splitting`).** The slice is
  large by *file count* (10 sub-checks across 5 Markdown files, 1 shipped spec, 2 `.py`
  docstrings, 2 DB apps, 4 render scripts) and is **zero** by boundary count, so the
  reviewer's load is prose reading, not proof auditing. The two halves *do* have different
  risk profiles — the generated half has concurrent-writer hazards and a different
  verification method (two-consecutive-regenerate byte-stability) than the prose half.
  **Ruling: do not split.** A split costs a spec edit, a plan-checklist regeneration by
  Worker 0, and a second full worker cycle at the very end of a build, and buys only an
  ordering guarantee that `### Sequencing constraints` already provides as a hard,
  recorded phase gate. Instead: **Phase A (prose + docstrings) must be complete and
  recorded before Phase B (generated docs + DB) begins**, and the build report states
  that the gate was observed.

### DRY analysis

**Helper inventory checked.** The package-wide AST inventory was refreshed this pass
(`docs/shadow/helper-inventory.md`, 1,626 lines, regenerated over all of
`django_strawberry_framework/` — not just `utils/`, per `worker-1.md`
`### Package-wide helper inventory before helper planning`). Shapes searched:
`deploy`, `migrat`, `guidance`, `docstring`, `glossar`, `tree`, `kanban`, `render`,
`regenerat`. Relevant candidates found: **none.** Every hit was an unrelated
value/SQL/plan renderer (`exceptions.py::describe_value`, `keyset.py::keyset_seek_sql`,
the optimizer's `_render_*` helpers). This slice writes **no Python logic at all**, so no
helper, constant, validation branch, coercion utility, or test helper is proposed, and
none is warranted. The condition that would change the answer: if a future slice needed
to *generate* rather than hand-author a doc section, the renderer would belong beside
`scripts/build_tree_md.py` — not in the package.

**Existing patterns reused.**

- The DB-then-regenerate pattern for `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md`
  (`scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`,
  `scripts/build_glossary_md.py`), and the docstring-then-regenerate pattern for
  `docs/TREE.md` (`scripts/build_tree_md.py`). Nothing new is authored; the existing
  scripts are the only writers of those four files.
- `apps/kanban/services.py::set_card_status` (`services.py:709-749`) is the **sanctioned
  writer** for a status change and is what prior card wraps used — `CardTransition` rows
  exist for `DONE-044-0.0.14` (`note="spec-044 Slice 3 joint 0.0.14 cut + card wrap"`) and
  `DONE-045-0.0.14` (`note="policy artifacts shipped"`), both `actor="maintainer"` (the
  only `Actor` row). Use the service, **not** a raw
  `card.status = …; card.save()`: it logs the transition atomically and stamps every
  unresolved incoming `blocked_by` edge `resolved_at`, which a bare save silently skips.
  The `pre_save` state-machine and done-invariant guards still fire either way.
- `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py` for the
  card↔term link sync. Read its `_load_rows` before running it: a CSV anchor with no
  `GlossaryTerm` row is a hard `CommandError`, and `--check` compares the card's link
  anchors to the CSV **as an ordered list**.

**New helpers justified.** None. Stated for the record rather than left silent.

**Duplication risk avoided — the doc-surface DRY ruling.** Six surfaces will describe the
same `asgi.py` + URLconf change. Repeated literals across docs are the real defect class
here, so the ownership is fixed now:

| surface | what it says | shape |
|---|---|---|
| `docs/README.md` `## Transport: the GraphQL HTTP endpoint and the ASGI router` | **THE canonical migration note.** The old-vs-new `asgi.py` pair, the `urlpatterns` entry, the three-row breaking-change table, the `APPEND_SLASH` policy. | **The only** full code recipe in the consumer-facing docs. |
| `docs/README.md` `### Transport deployment guidance` | **THE canonical deployment contract.** CSRF (incl. the `csrf_exempt`/`csrf_protect` ordering sentence), cache/`Vary`, security headers, IDE/GET, the two-layer body cap with the concrete proxy/ASGI directives, the multipart carve-out, the multipart control-document contract, the one-UTF-8-wire paragraph, revocation + Host + connection-lifetime. | The only place the concrete directives and numeric defaults appear. |
| `README.md` `## Status` | one-clause summary inside the `0.0.14` paragraph | prose only, **cross-references** `docs/README.md` via the existing `[readme]` def. No code block, no directives, no numeric caps beyond naming `MAX_REQUEST_BODY_BYTES` / `413`. |
| `TODAY.md` capability bullet `:384` | one-bullet summary | prose only, **cross-references** `docs/README.md` via the already-added `[readme-docs]` def. Same restraint. |
| `examples/fakeshop/test_query/README.md` | acceptance rows + the widened raw-envelope exemption | **not a migration surface.** It must not restate the recipe, the directives, or the caps. |
| `docs/SPECS/spec-041-…md` amendment banner | names the three superseded items + the `0.262.0`→`0.316.0` reconciliation, and points at `spec-046` | **not a migration surface.** No recipe, no code block. Point at the spec, not at `docs/README.md`. |
| `docs/GLOSSARY.md` entries (DB) | self-contained per-term definitions | glossary entries are self-contained **by design** (a reader lands on one anchor), so restating the composition and the constructor there is legitimate, not duplication. Still **no code block** and no proxy directives. |
| `views.py` / `routers.py` / `consumers.py` module docstrings | in-source reader's view | already written and **out of scope except** the one authorized `views.py` re-word. Legitimately restated for a different audience. |

**Repeated literals to state once and never re-type from another document.** Each must be
read from the source named, not copied from a sibling doc:

| literal | single source of truth | who may state it |
|---|---|---|
| `1_048_576` / "1 MiB" default | `conf.py::max_request_body_bytes` | `docs/README.md` deployment guidance, and the new glossary body-cap entry |
| `MAX_REQUEST_BODY_BYTES`, `413` | `conf.py` / `views.py` | `docs/README.md`; named (not explained) in `README.md` / `TODAY.md` |
| `r"^graphql/?$"` | `routers.py` `websocket_url_pattern` default | `docs/README.md` migration table (already correct on disk) |
| `4403` / `"Forbidden"` | `consumers.py:197-198` | `docs/README.md` revocation paragraph, and the new revocation glossary entry |
| the three-wrapper composition string | `routers.py:458-461` | `docs/README.md` (twice: the capability bullet and the injected-consumer sentence), `TODAY.md`, `README.md`, the router glossary entry — **five sites, and all five are wrong on disk today** |
| `client_max_body_size 1m` / `LimitRequestBody` / `request_buffer_size` | `docs/README.md` deployment guidance | that section **only** |

### Ruling 1 — `README.md`, `docs/README.md` and `TODAY.md` are this slice's own unfinished work

All three are **Slice 5 work that an interrupted pass left half-done**, not concurrent
work to leave alone. The build plan's `## Review round 2` already says so for the two
READMEs ("The partial `README.md` / `docs/README.md` edits already on disk are therefore
**unfinished Slice 5 work**, not round-2 work"); `TODAY.md`'s diff proves it belongs to
the same set (CORRECTION 2 above).

**Worker 2 completes all three.** It does **not** revert any of the existing edits, and it
does **not** rewrite what is already correct. The finishing work is corrective and
additive on top:

**`TODAY.md` — scoped to the single bullet at `:384` plus its link-def block.** Not a
maintainer item, not ambiguous: it is one hunk of this slice's own obligation, and the one
sentence in it that is factually wrong ("`AllowedHostsOriginValidator` over
`AuthMiddlewareStack` over a `URLRouter`") is wrong for the same round-2 reason as the two
READMEs. Worker 2 corrects that clause to the three-wrapper composition and touches
nothing else in the file. If any *other* hunk appears in `git diff -- TODAY.md` when
Worker 2 starts, that IS concurrent work: stop and report to Worker 0, never revert.

**What the finished three-wrapper story must say (the pre-round-2 shape is on disk in five
places).** `docs/README.md` mentions `AllowedHostsOriginValidator` at `:128`, `:283`,
`:316`, `:390`, `:398` and `DjangoWebSocketHostValidator` **zero** times. Every one of the
five, plus `TODAY.md:384` and `README.md:62`, currently documents a two-wrapper WebSocket
branch. The finished state states:

- The composition is **three** router-applied wrappers, outermost first —
  `DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(...))))`
  — and `DjangoWebSocketHostValidator` is a **private** package validator in
  `consumers.py`, not a public symbol a consumer imports or configures.
- **Host and Origin are two separate checks and neither substitutes for the other.**
  `Host` is validated by projecting the handshake's host metadata into a minimal Django
  `HttpRequest` and calling the public `request.get_host()`, so the project's existing
  `ALLOWED_HOSTS` and `USE_X_FORWARDED_HOST` govern the WebSocket handshake exactly as
  they govern HTTP, and **no new setting exists**. Only `DisallowedHost` becomes a denial,
  and the denial precedes authentication and consumer construction (Decision 19).
- The two sentences currently claiming that "the router's origin defence is
  `AllowedHostsOriginValidator`, not a CSRF token" (`docs/README.md:316`, `:398`) must
  name **both** wrappers. Leaving them Origin-only is exactly the round-2 finding-4 claim
  the maintainer rejected.
- The injected-consumer sentence at `:390` gains the third wrapper. Its two other claims
  are **true** and stay: an injected consumer opts out of the package's revalidation but
  never out of the wrappers, and a positive `websocket_revalidation_window` combined with
  `websocket_consumer_class` is a construction error (`routers.py:437-438`).
- The `asgi.py` code comment at `:283` ("`AllowedHostsOriginValidator >
  AuthMiddlewareStack > URLRouter > the consumer`") gains it too.

### Ruling 2 — the four mechanism paragraphs `docs/README.md` still owes

The spec's `## Doc updates` (`:2712-2732`) requires four paragraphs, each naming the
specific mechanism rather than a family. Measured: **all four are absent or wrong.**
`grep` over `docs/README.md` finds no `csrf_exempt`, no `csrf_protect`, no `FFFD`, no
`get_host`, no `USE_X_FORWARDED_HOST`, no `4403`.

1. **Revocation.** `:360` currently says the consumer "revalidates the session actor
   **before every operation**" — the pre-round-2 single-checkpoint claim, which
   Decision 16 falsified. Rewrite to the exact Decision-16 claim: revalidation happens at
   **two** checkpoints — operation admission and every information-bearing outbound
   operation frame (`next` / `data` / operation-scoped `error`) — so **a revoked actor can
   neither admit another operation nor emit another information-bearing operation frame**;
   detection is **event-boundary-driven**; the whole connection is closed (`4403` /
   `"Forbidden"`, with no preceding operation error) at whichever checkpoint notices
   first, **without a reconnect**; and `websocket_revalidation_window` now means the same
   thing at *both* checkpoints — the maximum age of a successful validation that may
   authorize a new operation or an information-bearing frame. Then, **stated and not
   implied**, the **idle-socket residue**: a revoked socket that produces no further
   events stays physically open, its subscription task, session object and stale actor
   reference occupying the server; that is DoS-relevant and **not** an authorization hole,
   and it is bounded by the deployment knobs the same paragraph names (Decision 12 +
   Decision 16 #"The idle-socket consequence"). The existing connection-lifetime
   paragraph's Daphne / nginx / upstream-`connection_init_wait_timeout` knobs are the
   knobs to point at — do not duplicate them.
2. **WebSocket Host.** New paragraph, per Ruling 1's four bullets.
3. **CSRF ordering.** New sentence in the `**CSRF.**` paragraph at `:316` that **leads
   with "ordering mechanism, not bypass"**: the view's dispatch callback is `csrf_exempt`
   on the outside so the global middleware's `process_view` cannot touch `request.POST`
   before the body gate, and a passing request then enters a package-owned continuation
   wrapped in Django's public `csrf_protect` — so full CSRF still runs and **the endpoint
   stays CSRF-protected even if a consumer omits the global `CsrfViewMiddleware`**. The
   spec is explicit that *"a reader who skims this paragraph must not come away thinking
   CSRF was relaxed"*, so the ordering claim must not be buried after the exemption.
4. **Multipart control documents.** New paragraph: `operations` / `map` must be
   **effectively UTF-8** and must **survive Django's decode without a replacement
   marker** — Django replacement-decodes malformed sequences to `U+FFFD`, so a literal
   `U+FFFD` in the serialized control value is refused with the same controlled `400`,
   before either value is parsed as JSON; genuine multibyte UTF-8 and ordinary
   `JSON.stringify` output are still accepted; and the `\uXXXX` **escape is named as the
   way to send a literal `U+FFFD`**. Django's `MultiPartParser`, `request.POST` /
   `request.FILES` and the upload handlers remain the sole owners of multipart parsing.

**Also in `docs/README.md`, and already partly right:** the multipart carve-out paragraph
exists but states only half of Decision 8's Slice-5 obligation. Add the second half — that
the **declaration is nonetheless enforced before that parser and its upload handlers
run**, which is a property of the view's `csrf_exempt` / `csrf_protect` ordering rather
than of the cap itself (Decision 8 `#"and, alongside it, the statement that"` +
Decision 18).

### Ruling 3 — the glossary DB: three rewrites, seven new terms, and the CSV stays at 37 rows

**Rewrites (three existing entries; their `title` and `anchor` are IMMUTABLE).** Changing
a heading changes its GitHub auto-anchor and breaks every
`GLOSSARY.md#<anchor>` link in the repo — including the 37 the spec itself carries, which
`scripts/check_spec_glossary.py` gates. Edit `GlossaryTerm.body` (and
`GlossaryTermLink` "See also" rows where a new term deserves a pointer); never `title`,
never `anchor`.

- `djangographqlprotocolrouter` (`docs/GLOSSARY.md:503-511`) — currently describes the
  superseded composition (`HTTP is AuthMiddlewareStack(URLRouter([graphql, *django_fallback]))`,
  `WebSocket is AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([graphql])))`),
  the byte-compatible constructor `(schema, django_application=None, url_pattern="^graphql")`,
  the prefix-matching `^graphql` note, and `strawberry-graphql>=0.262.0` inside the split
  install-hint sentence. Rewrite to: HTTP **is** the required `django_application`,
  dispatched directly; WebSocket is the three-wrapper composition; `django_application`
  required; `websocket_url_pattern` exact-by-default; the `websocket_consumer_class` /
  `websocket_revalidation_window` seams; and the hint's live `strawberry-graphql>=0.316.0`.
  Keep `**Status:**` at `shipped (\`0.0.14\`)` — the `0.0.15` status flip belongs to the
  joint cut (Decision 15), **not to this slice**.
- `channels-request-adapter` (`:314-322`) — **narrowed to WebSocket.** Its current body
  says `login` / `logout` "now run over Channels HTTP consumers too"; after Slice 1 the
  package router produces no GraphQL `http` scope at all, so a Channels HTTP scope reaches
  the auth boundary only from a consumer the project mounted itself (exactly what
  `auth/mutations.py`'s corrected docstrings now say — reuse that wording rather than
  inventing a second phrasing).
- `auth-mutations` — its transport matrix's **HTTP row** is corrected: GraphQL HTTP is the
  package's Django view in the consumer's URLconf, Django-CSRF-protected.

**Seven new terms.** One per capability the card authors, matching the spec's own list:
the package Django view (`DjangoGraphQLView` / `AsyncDjangoGraphQLView`), the cumulative
request-body cap, the strict UTF-8 wire contract, the WebSocket consumer-injection seam,
the revalidation window, the connection-scoped revocation contract, and the WebSocket Host
boundary. Each gets `status=shipped`, `status_text` matching the sibling `0.0.14` entries'
shape, a `body` written from the source (never from another doc), a
`GlossaryCategoryMembership` (`integration-tooling` for the router-adjacent five;
`permissions` for the revocation contract and the Host boundary — that is where
`channels-request-adapter` sits), and `GlossaryTermLink` "See also" edges to
`djangographqlprotocolrouter` / `configurationerror` as appropriate.

**Ordering mechanism for the insertion (this is the "dance", and it is minimal).** The
render orders terms by `["entry_order", "title_sort"]`, and `entry_order` is currently a
dense sequence that is monotone with `title_sort` (the rendered file is alphabetical).
So a new row assigned **the `entry_order` and `index_order` of its alphabetical
predecessor** lands in the right place: the tie breaks on `title_sort`, which is exactly
alphabetical. That leaves the 119 existing rows untouched — a minimal DB diff.
**Verify the premise before relying on it**: confirm `entry_order` is monotone with
`title_sort` across all 119 rows, and after the regenerate read the rendered position of
each of the seven new headings. If the premise does not hold, fall back to a deterministic
re-rank over `title_sort` for both `entry_order` and `index_order`, and record the wider DB
diff explicitly in the build report rather than letting it look like churn.

**The CSV stays at 37 rows, and Worker 2 does not touch it.** `scripts/check_spec_glossary.py`
requires, for **every** CSV row, that the *spec* link that anchor — so growing the CSV
forces seven new `[term][glossary-…]` uses plus seven link defs **in the spec**, which
only Worker 1 may write and which is frozen this pass. The spec's own `## Key glossary
references` is scoped to "terms this spec **relies on**"; the seven new terms are terms
the card **authors**, which the spec references by *Decision* rather than by glossary link.
Leaving the CSV at 37 keeps `check_spec_glossary.py` at `OK: 37 terms` / exit 0 and
`import_spec_terms --check` at `OK: … done cards have glossary links`, while
`docs/GLOSSARY.md` still gains all seven entries — which is what the spec's Doc-updates
bullet actually requires. **Rejected alternative:** grow the CSV to 44 and have Worker 1
add the seven spec link uses at final verification. Rejected because it leaves
`check_spec_glossary.py` failing between Worker 2's CSV edit and Worker 1's spec edit, and
it puts a DB write plus three regenerates inside a final-verification pass, which is not a
builder pass. Recorded as a candidate for `bld-final.md`'s
`### Deferred work catalog` rather than silently dropped — see `### Notes for Worker 1`.

### Ruling 4 — the card body: three text corrections, five DoD ticks, one deliberate non-tick

Measured card `65` items: 5 `scope`, 6 `definition_of_done`, 6 `arch_posture`,
6 `why_it_matters`, 7 `test_plan`, 3 `open_question` — **all 33 with `is_complete=False`**.

**Text corrections — exactly three**, each because a decided contract falsified the
sentence (the same standard Decision 14 applies to `spec-041`):

- `scope` order `3` — "per-operation session revalidation hook (reload the actor before
  execution; …)". Correct to the two-checkpoint, connection-scoped-revocation contract.
- `definition_of_done` order `3` — "WebSocket **per-operation** session revalidation via
  the injection seam." Same correction.
- `arch_posture` order `3` — "exact GraphQL route -> AllowedHostsOriginValidator ->
  AuthMiddlewareStack …". Correct to the three-wrapper composition with
  `DjangoWebSocketHostValidator` outermost.

**Leave alone:** every `why_it_matters` item (they record the audit findings that motivated
the card and are historical), `arch_posture` order `0`'s "RECOMMENDED DIRECTION
(maintainer-pinned…)" framing, every `test_plan` item, and — explicitly — **all three
`open_question` items.** Decisions 7, 6 and 10 answered them, but an open question records
what was open when the card was written; the spec's Decisions are the answer, and the
repo's shipped-card convention is that the Status line and the spec are the source of
truth. Deleting or rewriting them is churn with no correctness gain.

**DoD ticks.** Set `is_complete = True` on `definition_of_done` orders `0`, `1`, `2`, `3`,
`4`. Leave `verified_at` / `verified_by` / `verification_kind` **null** — the only `Actor`
row is `maintainer`, and inventing a worker actor is scope creep.

**Leave `definition_of_done` order `5` — "Full suite green at 100% coverage
(maintainer/CI gate); ruff + trailing-comma clean; manage.py check + makemigrations
--check clean" — at `False`.** Two reasons, and the spec's own deferral overrides the
mark-every-DoD convention here: (a) `BUILD.md` `## Coverage is the maintainer's gate, not
a worker's tool` forbids any worker from running or asserting coverage, so no worker can
truthfully tick a 100%-coverage box; (b) the full-suite / `ruff` / `manage.py check` /
`makemigrations --check` sweep runs in `## Final test-run gate`, i.e. **after** Slice 5.
The done-card DB invariant is only `SpecDoc` + ≥1 `CardGlossaryTerm`, so the flip succeeds
with this box unticked, and `KANBAN.md` renders it unticked — which is correct and is the
repo's convention (the Status line is the source of truth). Worker 1 records the one-line
deferral at final verification; routed to the maintainer as the tick's owner.

### Ruling 5 — `spec-041`: the banner, and a per-occurrence ruling on all eleven `0.262.0` mentions

**Banner.** Immediately under `spec-041`'s title (before its opening `Planned for 0.0.14`
paragraph), naming `spec-046` and listing **exactly** the three superseded items from
Decision 14 — Decision 6 (constructor parity, superseded in full), Decision 2's **HTTP
half** (card-scope boundary), and the **Borrowing posture**'s HTTP-branch /
Django-fallback paragraphs — plus, stated as **explicitly not a supersession**, the
`0.262.0` → `0.316.0` reconciliation of factually-wrong live-code prose. Decision 14
requires the banner to say so "rather than listing it beside the three superseded items".

Reference-style per `AGENTS.md`: add `[spec-046]: ../spec-046-transport_security-0_0_15.md`
under `spec-041`'s existing `<!-- docs/ -->` group (alphabetical: after
`[glossary]` / `[glossary-*]`, before `[tree]`). The 10 canonical group headers are already
present in that file.

**Do NOT rewrite `spec-041`'s opening paragraph** ("wiring GraphQL onto **both** HTTP and
WebSocket in one import"). It is not one of the three superseded items, it is a true
description of what that card shipped, and the banner sits **above** it so the reader hits
the supersession first. Checkbox state everywhere in `spec-041` is left **exactly** as it
is; the Status line remains the source of truth.

**The eleven `0.262.0` mentions, classified. Six corrections, five keeps.** Worker 2
applies this table and reports any disagreement in `### Notes for Worker 1` rather than
deviating.

| `spec-041` line | what the sentence claims | ruling |
|---|---|---|
| 24 | "already inside the package's pinned `strawberry-graphql>=0.262.0` floor" | **CORRECT → `>=0.316.0`.** A live claim about the package's pinned floor. The rest of the sentence ("the floor-version presence is upstream history, re-confirmed at the Slice-1 dependency gate") is historical and stays. |
| 173 | "the 0.262.0-floor presence is upstream history, re-confirmed at the dependency gate" | **KEEP.** Explicitly historical. |
| 265 | "the Strawberry `0.262.0`-floor consumer check becomes an explicit Slice-1 gate item + DoD line" | **KEEP.** Names the build step that was performed, not the live floor. |
| 339 | "a `strawberry.channels` consumer failure names **both** `channels>=4.3.2` and `strawberry-graphql>=0.262.0`" | **CORRECT → `>=0.316.0`.** Describes the live `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT`, which Slice 4 re-pinned. |
| 498 | "import at the package's pinned `strawberry-graphql==0.262.0` floor (with channels installed)" | **KEEP.** A Slice-1 checklist row recording the version a past gate ran at. Decision 14's mandate is narrow ("factually-wrong prose only"); over-editing a shipped card's checklist is the worse error. |
| 672 | "its presence back at the pinned `strawberry-graphql>=0.262.0` floor is upstream history, spot-checked at the dependency gate" | **KEEP.** Explicitly historical. |
| 927 | Error-shapes section: the broken-install message "names **both** … `strawberry-graphql>=0.262.0`" | **CORRECT → `>=0.316.0`.** Describes the live error string. |
| 1148 | same live error string, restated in the helper/error section | **CORRECT → `>=0.316.0`.** |
| 1258 | "present at the package's pinned `strawberry-graphql>=0.262.0` floor" | **CORRECT → `>=0.316.0`.** A live claim about the pinned floor. |
| 1260 | "the export's presence at the 0.262.0 floor itself is upstream history, spot-checked at the dependency gate" | **KEEP.** This is the sentence the spec quotes verbatim as its own example of what stays. |
| 1868 | test description: symbol access "raises … naming **both** `channels>=4.3.2` and `strawberry-graphql>=0.262.0`" | **CORRECT → `>=0.316.0`.** Describes the live assertion Slice 4 re-pinned in `tests/test_routers.py`. |
| 2048 | DoD: "confirmed importable at `strawberry-graphql==0.262.0` in an isolated throwaway venv" | **KEEP.** Records what the shipped card verified; checkbox state untouched. |

**No new Python 3.10 problem is behind any of this** (Decision 14's own words): the
dependency floor in `pyproject.toml` and the minimum CI matrix node already agree on
`0.316.0`. Verify that from `pyproject.toml` and the CI matrix file, not from a document.

### Sequencing constraints

The spec pins one. Six more were found this pass. **Phase A must be fully complete and
recorded before Phase B starts.**

1. **Every `.py` docstring edit lands before the `docs/TREE.md` regenerate.** The spec
   names the `test_transport_api.py` case; the general rule is what matters, because
   `build_tree_md.py` renders each module's **first docstring line** and `--check`
   currently already fails. Verified this pass: all four package modules and both test
   modules have a period-terminated first line, so the render will not reject one
   (`build_tree_md.py` rejects a first line that is not a period-terminated sentence).
   `test_transport_api.py`'s first line is already correct at `HEAD` (verify only).
2. **`tests/test_views.py`'s first docstring line is corrected before the same
   regenerate.** It reads `(spec-046 Slice 1)` but the file now carries Slice 2's cap
   rows, Slice 3's wire rows and round 2's additions, and the TREE regenerate will publish
   that line into a standing doc **for the first time**. `ARTIFACT.md`
   `### Documentation / release sanity` requires the feeding docstring fix and the
   regenerate to land in the **same** change. The spec's `## Doc updates` names
   `tests/test_views.py` as a TREE row this slice adds and the Slice-2-prose sub-check
   already names the file, so it is in scope. Correct it to the file's actual slice scope
   (provenance, per `ARTIFACT.md`'s keep-provenance/scrub-staging distinction — do not
   delete the `spec-046` citation).
3. **The `views.py` mixin-docstring re-word lands before the regenerate too** (same phase
   rule), though it targets `_RequestBodyBoundaryMixin`'s class docstring, not the module
   first line, so it cannot change the rendered row.
4. **`docs/README.md`'s in-page anchor targets must exist before anything links to them.**
   `README.md`, `TODAY.md` and `docs/README.md:398` already link
   `#transport-the-graphql-http-endpoint-and-the-asgi-router`. That heading exists on
   disk; if Worker 2 renames or re-nests any heading in that section, every one of those
   links breaks. **Do not rename the existing headings.**
5. **The `CardGlossaryTerm` bootstrap lands before the status flip** — the `pre_save`
   guard raises `DONE_CARD_GLOSSARY_ERROR` otherwise, and `glossary_links` is `0` today.
6. **`import_spec_terms` runs after the flip and before all three regenerates.** It only
   processes `status__key="done"` cards, so it cannot see card 65 until the flip; and its
   `GlossarySpecMention` rows feed `build_glossary_md.py`'s
   `allGlossarySpecMentions` query, so `docs/GLOSSARY.md` is stale if it runs after.
7. **The seven new `GlossaryTerm` rows and the three rewrites land before
   `build_glossary_md.py`.** And `scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md`
   runs **after** the regenerate — it is the gate that catches a broken anchor from a
   changed heading.

Two non-constraints, recorded so nobody invents them: the card flip has **no** effect on
`docs/TREE.md` (card 65 has zero `TrackedPath` rows, and planned paths already on disk are
skipped regardless of card status), and `spec-041`'s banner has no dependency on
`docs/README.md`.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against the current source
before editing, since another pass may have shifted a file.

**Phase A — prose and docstrings.**

1. **Verify-only, report, do not edit** (the five/six rows in the preamble table):
   `auth/sessions.py::classify_transport`, `auth/mutations.py::_login_resolve_body` and
   `::_logout_resolve_body`, `conf.py`'s `MAX_REQUEST_BODY_BYTES` comment,
   `tests/test_views.py`'s mixin-privacy test, and
   `test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce`'s
   docstring. State in the build report that each satisfies its bullet, quoting the
   satisfying text. **Never revert them.** A needed *additional* correction to any of them
   is a report-to-Worker-0 item, not a silent edit.
2. **`django_strawberry_framework/views.py`**, `_RequestBodyBoundaryMixin` class docstring
   (`views.py:369-372`): replace the non-operative "so `max_request_body_bytes` is already
   a class attribute by the time Django's `View.as_view` runs its `hasattr` keyword guard"
   rationale with the operative one — **the mixin's attribute and its methods must take
   precedence over any same-named attribute upstream may later add** — and keep the
   already-correct trailing clause about a consumer subclass overriding any part.
   The `as_view` keyword guard is a `hasattr` over the whole MRO, so a mixin-**last**
   subclass would bind `max_request_body_bytes=` identically; that is why the old reason is
   non-operative. Check that the `#:` comment at `views.py:453` ("rather than on each view
   so Django's `as_view` keyword guard admits it") stays coherent — that one **is** true
   and operative (it is about *where* the attribute is declared, not about ordering) and
   should be left alone. ASCII-only.
3. **`tests/test_views.py`** first docstring line — per sequencing constraint 2.
4. **`docs/README.md`** — complete the section already on disk:
   - the three-wrapper corrections at `:128`, `:283`, `:316`, `:390`, `:398` (Ruling 1);
   - the four mechanism paragraphs, and the Decision-8 second half (Ruling 2);
   - re-read the whole `## Transport…` + `### Transport deployment guidance` block
     end-to-end afterwards for any other pre-round-2 residue.
5. **`README.md`** `## Status` — the paragraph is largely finished; correct the
   WebSocket-composition clause to the three-wrapper shape and confirm the paragraph makes
   no claim the DRY table assigns elsewhere (no code recipe, no proxy directives).
   Note the existing hunk mixes `-` where the surrounding prose uses em dashes; normalize
   to the file's convention while you are in the sentence.
6. **`TODAY.md`** — the single bullet at `:384` (Ruling 1). Nothing else.
7. **`docs/SPECS/spec-041-channels_router-0_0_14.md`** — the banner, the link def, and the
   six corrections from Ruling 5's table.
8. **`examples/fakeshop/test_query/README.md`** — add the **S1 and S2** acceptance rows
   alongside S9's (the file does not mention `test_transport_api.py` at all today, so S1's
   rows are owed as well as S2's), and **widen the raw-envelope exemption at `:5`.** Its
   current wording exempts only "malformed bodies, content-type negotiation", which does
   not cover: S1's hostile-`Host` / `secure=` / `enforce_csrf_checks=` / `AsyncClient`
   rows; S2's in-process `ASGIHandler` driver for the unmeasured / understated /
   fragmented-body rows; the real-`multipart/form-data` control-field rows (Decision 17);
   or the `Client(enforce_csrf_checks=True)` ordering row with its parser sentinel
   (Decision 18). The spec is explicit that **the file must say so rather than leaving a
   reader to infer it from the absence of a row.** Keep the file's existing narrative
   register and its link-def block's 10 group headers. No migration recipe here.
9. **Record the Phase A gate** in the build report before starting Phase B.

**Phase B — generated docs and the DB.** Never reset `examples/fakeshop/db.sqlite3`; apply
every write on top. Write kanban and glossary rows through the **Django ORM**
(`uv run python examples/fakeshop/manage.py shell`), never raw SQL — both render scripts
run an in-process `/graphql/` query requesting `uuid { id }`, which needs the `post_save`
`UUIDModel` side-row a raw insert skips.

10. **`docs/TREE.md`**: `uv run python scripts/build_tree_md.py`. Expect new rows for
    `views.py`, `_request_body.py`, `consumers.py`, `utils/sessions.py` and
    `tests/test_views.py` in **both** the current and target package layouts and both test
    trees, plus a corrected `routers.py` row (its module docstring first line already reads
    `Channels ASGI router: Django owns HTTP, the package composes WebSocket (spec-046).`).
    Then `--check` to confirm it is now up to date.
11. **Glossary DB**: the three rewrites and the seven new terms (Ruling 3). Verify the
    `entry_order` monotonicity premise first.
12. **Kanban DB**: verify the `SpecDoc` url (already correct); bootstrap **one**
    `CardGlossaryTerm` for an anchor **in the CSV** (`djangographqlprotocolrouter` — pick
    one in the CSV so `import_spec_terms` reconciles rather than deletes it); apply the
    three `CardItem.text` corrections and the five DoD ticks (Ruling 4); then flip via
    `apps.kanban.services.set_card_status(card, "done", actor="maintainer", note=…)`.
13. **`uv run python examples/fakeshop/manage.py import_spec_terms`** (write mode). It
    processes **every** done card and creates `CardGlossaryTerm` + `GlossarySpecMention`
    rows from each card's CSV, so the resulting `db.sqlite3` diff can legitimately span
    more than card 046. **Flag the wider diff in the build report; do not treat it as a
    defect and do not try to narrow it.**
14. **Regenerate all three, from the repo root**: `scripts/build_kanban_md.py`,
    `scripts/build_kanban_html.py`, `scripts/build_glossary_md.py`. `KANBAN.html`'s Vue
    shell is hand-edited and only its data block regenerates — do not touch the shell.

### Test additions / updates

**No test is added or changed by this slice, and none should be.** The slice ships prose,
generated docs and DB rows; the assertions it describes were all landed and accepted by
Slices 1-4 and review rounds 1-2. The only `.py` edits are docstring text.

Focused runs that confirm nothing regressed (no `--cov*` flags, ever):

- `uv run pytest tests/test_views.py --no-cov` — the one test file whose bytes change.
- `uv run pytest examples/fakeshop/apps/kanban examples/fakeshop/apps/glossary --no-cov` —
  the two apps whose DB rows change, so a model-level invariant break surfaces here rather
  than at the final gate.
- `uv run pytest examples/fakeshop/test_query/test_kanban_api.py examples/fakeshop/test_query/test_glossary_api.py --no-cov`
  — the live tier over those two apps' schemas.
- `uv run python examples/fakeshop/manage.py check`.

**Verification the build report must carry** (a single `git diff` is **not** proof —
`BUILD.md` `### Tracked binary / generated files`):

- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: N done
  cards have glossary links.` (baseline was `OK: 45`; expect `46`).
- **Two-consecutive-regenerate byte-stability** for each of `docs/TREE.md`,
  `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`: run each script twice, `cmp` the two
  outputs. This is the real proof; a clean `git diff` is not available on a slice that
  legitimately diverges the DB from `HEAD`.
- `uv run python scripts/build_tree_md.py --check` → up to date.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md`
  → `OK: 37 terms`, exit 0. (Baseline at pre-flight was the same; a regression here means
  a rewritten heading changed an anchor.)
- `KANBAN.md` shows `DONE-046-0.0.15` in the **Done** section, absent from its old
  section, with `definition_of_done` boxes 0-4 ticked and box 5 unticked.
- `git status --short` after every write-mode run: every modified file must be
  slice-intended and appear in `### Files touched`. Anything else is a
  **stop-and-report**, never a revert.

**Temp/scratch tests: none appropriate.** Nothing here is a boundary, so there is nothing
for Worker 3 to demonstrate as non-distinguishing. Worker 3's most valuable review here is
reading the finished prose against `routers.py:458-461`, `consumers.py:197-198` /
`:12-56`, `views.py`'s cap docstring and `conf.py:112-131` — i.e. checking every claim
against the shipped guard body, not against a sibling document.

### Validation commands

- `uv run ruff format django_strawberry_framework/views.py tests/test_views.py`
- `uv run ruff check --fix django_strawberry_framework/views.py tests/test_views.py`
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/views.py tests/test_views.py README.md TODAY.md docs/README.md docs/SPECS/spec-041-channels_router-0_0_14.md examples/fakeshop/test_query/README.md`
  — the `.md` half is the **link-definition-scaffold** check (all 10 group headers, in
  order) plus fenced-`json`/`graphql` normalization; the `.py` half is trailing-comma
  layout plus the ASCII-only report.

**Both of these tools MUST be given explicit paths.** `check_trailing_commas.py` defaults
to a repo-wide **auto-fix**, which would rewrite the maintainer's untracked `drys.md` /
`vulns.md`, and `check_spec_glossary.py` likewise takes an explicit `--spec`.
`docs/builder/` is in `EXCLUDE_SCRATCH_DIRS`, so this artifact is not subject to the
scaffold check.

**Scoped `ruff` is an open reconciliation, not a settled rule.** All four role files tell
workers to scope the write-mode `ruff` runs to their own files because this tree carries
concurrent uncommitted work, while `AGENTS.md:15` mandates the repo-wide form and the role
files defer to `AGENTS.md` on conflict — so the scoping instruction is inert until the
maintainer reconciles it (build plan `## Open maintainer decisions`). **Worker 2 raises
this in its build report rather than resolving it**, and uses the scoped form given above
in the meantime.

### Files Worker 2 may write — this list is exhaustive

| file | why |
|---|---|
| `docs/README.md` | migration note + transport deployment guidance (sub-checks 1, 2) |
| `README.md` | transport wording (sub-check 4) |
| `TODAY.md` | transport wording (sub-check 4) — the `:384` bullet and its link-def block only |
| `docs/SPECS/spec-041-channels_router-0_0_14.md` | amendment banner + the six `0.262.0` corrections (sub-check 3) |
| `docs/TREE.md` | **regenerate only**, via `scripts/build_tree_md.py` (sub-check 4) |
| `docs/GLOSSARY.md` | **regenerate only**, via `scripts/build_glossary_md.py` (sub-check 4) |
| `KANBAN.md`, `KANBAN.html` | **regenerate only** (sub-check 9); `KANBAN.html`'s Vue shell is hand-edited and stays |
| `examples/fakeshop/db.sqlite3` | via the **Django ORM** only; never reset (sub-checks 4, 9) |
| `django_strawberry_framework/views.py` | the one authorized docstring re-word (sub-check 7) |
| `tests/test_views.py` | the docstring first line (sequencing constraint 2) |
| `examples/fakeshop/test_query/README.md` | acceptance rows + widened exemption (sub-check 6) |
| `docs/builder/bld-slice-5-docs_foldin.md` | its own build report + checklist ticks |
| `docs/builder/worker-memory/worker-2.md` | its memory |

### Files Worker 2 must NOT touch

- **`docs/spec-046-transport_security-0_0_15.md` and
  `docs/spec-046-transport_security-0_0_15-rationale.md`** — custodian-only; Worker 2 never
  edits the spec and **never reads the rationale companion**. Required wording goes in
  `### Notes for Worker 1 (spec reconciliation)` **on disk**, not only in the return report:
  round 1's custodian had to re-derive a list that never reached disk.
- **`docs/spec-046-transport_security-0_0_15-terms.csv`** — stays at 37 rows (Ruling 3).
- **The maintainer's incoming review document** — evidence, never edited, never
  annotated, never ticked.
- **`drys.md`, `vulns.md`** (untracked maintainer scoping notes) — never touch. This is
  the concrete reason the `check_trailing_commas.py` invocation above carries explicit
  paths.
- **`docs/builder/build-046-transport_security-0_0_15.md`** — Worker 0's file, including
  every slice checkbox.
- **Every other `docs/builder/bld-*.md`**, and in particular
  **`docs/builder/bld-review-2-w3_residual.md`**, which a Worker 3 pass wrote or is
  writing concurrently — do not read it as evidence for this slice, do not touch it.
- **`docs/builder/worker-memory/worker-0.md` / `-1.md` / `-3.md`.**
- **`CHANGELOG.md`** — no edit, and no permission for one exists in this card
  (Decision 15; `AGENTS.md` L21).
- **The version quintet** — `pyproject.toml [project].version`,
  `django_strawberry_framework/__init__.py::__version__`, `tests/base/test_init.py`, and
  the `CHANGELOG.md` entry. Card `045` is still `todo` at `0.0.15`, so the joint cut owns
  the quintet (Decision 15). Related and equally out of scope: the `shipped (0.0.15)`
  status flip and the "Coming next" → "Shipped today" move in `README.md` / `TODAY.md`, and
  the `**Status:**` line of any glossary entry.
- **`django_strawberry_framework/routers.py`, `consumers.py`, `_request_body.py`,
  `conf.py`, `auth/sessions.py`, `auth/mutations.py`, `_strawberry_patches.py`,
  `_cross_web_patches.py`** — read them (they are the source of truth for every claim the
  prose makes) but change nothing. The `auth/` and `conf.py` files are also on the
  do-not-revert list.
- **`tests/test_routers.py`, `examples/fakeshop/test_query/test_transport_api.py`,
  `tests/auth/test_mutations.py`, and every other test file** — no assertion changes; the
  rows stay exactly as accepted. `test_transport_api.py`'s docstring is already correct.
- **`docs/SPECS/spec-041`'s checkbox state and its opening paragraph** (Ruling 5).
- **`docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html` as text** — these are
  rendered. A hand-edit is silently reverted by the next render. Edit the DB or the
  docstring, then regenerate.
- **`GOAL.md`, `SECURITY.md`, `BACKLOG.md`, `uv.lock`, `pyproject.toml`** — the spec's
  `## Doc updates` lists them (or their concerns) as untouched.
- **Any `GlossaryTerm.title` or `.anchor`** — immutable; changing one breaks every
  `GLOSSARY.md#anchor` link in the repo.
- **`git`**: no commit, branch, stash, `git add`, `git checkout`, `git restore`, or
  `git worktree`. Only the maintainer commits.

### Implementation discretion items

Assessed and decided to be Worker 2's:

- The exact **sentence order and paragraph boundaries** of the four new mechanism
  paragraphs inside `### Transport deployment guidance`, provided each names its specific
  mechanism and the CSRF paragraph leads with "ordering mechanism, not bypass".
- The exact **prose of the seven new glossary bodies**, provided each is written from the
  source module and reuses the phrasing already shipped in the corresponding docstring
  rather than inventing a second wording for the same contract.
- Whether the **WebSocket Host** material is a new sub-heading or a paragraph inside the
  existing guidance block — as long as no **existing** heading is renamed (sequencing
  constraint 4).
- The **`note=` text** on `set_card_status`, and the exact wording of the three
  `CardItem.text` corrections.
- Whether the seven new terms take **`GlossaryAlias`** rows. None is required; add one only
  where a genuinely different prose spelling is already in use in the docs.

### Notes for Worker 1 (spec reconciliation)

Recorded now, for the final-verification pass. **The spec is frozen this pass and none of
these was acted on.**

1. **The Slice-5 sub-check at `:329-338` is factually stale.** It asserts
   `test_transport_api.py`'s module docstring first line "still scopes the file to
   `(spec-046 Slices 1-2)`". It reads `(spec-046 Slices 1-3)` on disk **and at `HEAD`**.
   The sub-check's *instruction* ("correct it to the file's actual slice scope … before the
   `docs/TREE.md` regenerate") is still the right instruction and is satisfied; only the
   premise sentence is wrong. Candidate for a one-clause correction at final verification.
2. **The `## Doc updates` GLOSSARY bullet and Worker 0's dispatch findings disagree**, and
   the bullet wins: seven net-new terms are required (CORRECTION 3). Worth a sentence in
   the spec only if the maintainer wants the requirement made unmissable; the bullet
   already says it.
3. **The seven new glossary anchors are deliberately absent from the terms CSV**
   (Ruling 3). If the maintainer wants card 046's `CardGlossaryTerm` link set to include
   the terms it authored, that is a **Worker-1 pass** editing the CSV **and** the spec's
   `## Key glossary references` + link-def block together, followed by a re-run of
   `import_spec_terms` and `build_glossary_md.py`. Route to `bld-final.md`'s
   `### Deferred work catalog`; do not let it fall out silently.
4. **`definition_of_done` order `5` is left unticked by design** (Ruling 4). Worker 1
   records the one-line deferral; the tick's owner is the maintainer, after the final gate.
5. **Worker 0's dispatch prompt contained three wrong facts** — `utils/sessions.py`'s TREE
   row, `TODAY.md`'s attribution, and the "seeding new glossary terms is a no-op" finding.
   Worth carrying into the closeout retrospective as evidence that a dispatch-prompt
   finding is a hypothesis to re-verify, exactly as a review's prescribed remediation is.
6. **`M4` and `M5` remain open maintainer escalations** and were not touched. This slice's
   own declarations are `none` for both floor verification and hot path, which does not and
   cannot resolve the build-wide ones.
7. **Two BINDING cross-slice integration items** are still outstanding in
   `examples/fakeshop/test_query/test_transport_api.py` (extract a shared
   `_user_who_can_add_categories()` helper across its 2 sites; rewire the six inline
   `await ….post(...)` blocks onto the existing `_post_bytes`). They belong to the
   **integration pass**, not to this slice, and this slice deliberately touches no test
   assertions.
8. **Closed `docs/review/`, `docs/dry/` and `docs/bug_hunt/` scratchpads still assert the
   old "UTF-16 succeeds" contract.** Leave them; carry to `bld-final.md` as a
   "do not act" catalog entry.

### Spec slice checklist (verbatim)

- [x] **Slice 5 — S12 transport slice: migration note, deployment guidance, doc fold-in**
  - [x] The migration note: old vs new `asgi.py` **plus** the required Django
        `urlpatterns` entry, in [`docs/README.md`][docs-readme].
  - [x] Transport deployment guidance: CSRF, cache / `Vary`, security headers, IDE and
        GET controls, and the body-limit deployment expectation — which is where the
        reverse-proxy / ASGI-server cap is stated as a **co-requirement** for the
        consumer, with its concrete directives (`client_max_body_size` on nginx, the
        ASGI-server equivalents, the Daphne request-buffer note) and with the multipart
        carve-out named, so a reader of the proxy-cap paragraph alone cannot conclude that
        multipart is byte-counted
        ([Decision 8](#decision-8--the-deployment-layer-cap-is-a-co-requirement-not-an-alternative)).
  - [x] [`spec-041`][spec-041] amended in place with an amendment banner naming the three
        superseded decisions
        ([Decision 14](#decision-14--this-card-amends-spec-041-and-supersedes-three-of-its-decisions)),
        **and** its historical `strawberry-graphql>=0.262.0` floor prose reconciled to the
        live `>=0.316.0` requirement in the same pass. That spec is **shipped**, so the
        reconciliation corrects only factually-wrong prose — the sentences that describe the
        package's *current* dependency floor and the CI node that pins it — while checkbox
        state is left exactly as it is and the Status line remains the source of truth,
        which is this repo's shipped-card closeout convention. Sentences that are explicitly
        historical ("the export's presence at the 0.262.0 floor itself is upstream history,
        spot-checked at …") stay: they record what was true when that card shipped and are
        not claims about live code. There is no new Python 3.10 problem behind this: the
        dependency floor and the minimum CI matrix node already agree on `0.316.0`. The
        `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT` string and the
        `tests/test_routers.py` assertion that pins it are corrected by Slice 4's own
        change, not here — this bullet owns the shipped spec's prose only.
  - [x] [`docs/GLOSSARY.md`][glossary] via the glossary DB + re-render (never
        hand-edited); [`docs/TREE.md`][tree] regenerated for **all four** modules the
        earlier slices added — `views.py`, `_request_body.py`, `consumers.py`, and
        `utils/sessions.py` — in both the current and target package layouts, plus the new
        tests; [`README.md`][readme] / [`TODAY.md`][today] transport wording. The render
        reads each module docstring's first line, so a module whose docstring is missing
        fails the regenerate rather than silently omitting the row.
  - [x] The three now-wrong transport strings in `django_strawberry_framework/auth/`,
        corrected in the same pass as the prose above: `sessions.py::classify_transport`'s
        unrecognized-scope-type `ConfigurationError` (it tells the reader to "route GraphQL
        through `DjangoGraphQLProtocolRouter`", which after Slice 1 produces no GraphQL
        `http` scope at all), and the `mutations.py::_login_resolve_body` /
        `::_logout_resolve_body` docstrings that describe "the package router's async
        consumer" (the package router no longer has an HTTP consumer of either colour).
        Prose only, no behavior change; none is load-bearing, and they are outside the
        named files of every earlier slice, which is why they route here.
  - [x] `examples/fakeshop/test_query/README.md`: the **S1 and S2** acceptance rows (the
        file does not mention `test_transport_api.py` at all today) alongside S9's, **plus**
        a widened raw-envelope exemption — its current wording exempts only "malformed
        bodies, content-type negotiation" from the shared harness, which does not cover the
        hostile-`Host` / `secure=` / `enforce_csrf_checks=` / `AsyncClient` rows S1 added or
        the in-process `ASGIHandler` driver S2 added for the unmeasured / understated /
        fragmented-body rows. The exemption widens again for the
        real-`multipart/form-data` control-field rows
        ([Decision 17](#decision-17--multipart-control-fields-stay-django-parsed-behind-a-strict-loss-detection-guard))
        and the `Client(enforce_csrf_checks=True)` ordering row with its parser sentinel
        ([Decision 18](#decision-18--the-body-gate-runs-before-djangos-multipart-parser-via-view-local-csrf-re-entry))
        are both outside the shared harness, and the file must say so rather than leaving a
        reader to infer it from the absence of a row.
  - [x] The Slice-2 prose corrections, carried here for the same reason as the `auth/`
        strings above (prose only, none load-bearing, none in a Slice-2 named file's
        contract): `views.py`'s cap-contract docstring re-words its mixin-first rationale
        to the operative reason — the mixin's attribute and method must take precedence
        over any same-named attribute upstream may later add — rather than the
        non-operative claim that the ordering is what satisfies `View.as_view`'s keyword
        guard (that guard is a `hasattr` over the whole MRO, so a mixin-**last** subclass
        binds `max_request_body_bytes=` identically); `conf.py`'s `MAX_REQUEST_BODY_BYTES`
        comment gains the multipart carve-out so the surface a consumer configures does not
        claim counted bytes where the bound is the declaration alone; the trivially-true
        `mixin.__name__ not in __all__` assertion in `tests/test_views.py`'s mixin-privacy
        test is dropped, leaving the exact-`__all__` test as the single privacy proof; and
        `test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce`'s
        docstring drops its "the spec's Edge-case sentence predicting a `413` is inaccurate"
        clause, which the spec's corrected Edge-case sentence has made obsolete —
        the `400` explanation itself stays, since it is the reason the row asserts what it
        asserts.
  - [x] The Slice-3 prose correction, in
        `examples/fakeshop/test_query/test_transport_api.py` and carried here for the same
        reason as the Slice-1 and Slice-2 prose above: the module docstring's **first line**
        still scopes the file to `(spec-046 Slices 1-2)` although it now also carries the
        S9 async rows and the wire contract's kill-switch rows — correct it to the file's
        actual slice scope, and do it **before** the [`docs/TREE.md`][tree] regenerate in
        this same slice, because that first line is the text `scripts/build_tree_md.py`
        renders (pinning a number at Slice 3 would have been a guess about a file Slice 4
        could still add rows to; pinning it here pins the truth). No assertion changes; the
        rows stay exactly as accepted.
  - [x] Card flip to Done + `KANBAN.md` / `KANBAN.html` regeneration from the DB.
  - [x] **No version quintet movement, and no `CHANGELOG.md` edit**
        ([Decision 15](#decision-15--the-0015-version-bump-is-deferred-to-the-joint-cut)).

---

## Build report (Worker 2)

Phase A (prose + docstrings) was completed and recorded **before** Phase B (generated docs +
DB) began, as `### Sequencing constraints` requires. The Phase A gate is the block ending
"Phase A gate" below; nothing in Phase B was started until every item above it had landed and
`ruff` + `check_trailing_commas --check` + `git status --short` + `uv run pytest
tests/test_views.py --no-cov` (144 passed) were green on the Phase A diff alone.

### Files touched

Grounded in `git status --short` taken after both `ruff` invocations and again after the last
regenerate. Every line below is on the artifact's `### Files Worker 2 may write` list.

- `django_strawberry_framework/views.py` — **two** docstring edits, prose only, no behavior
  change. (1) `_RequestBodyBoundaryMixin`'s class docstring: the non-operative "so
  `max_request_body_bytes` is already a class attribute by the time Django's `View.as_view`
  runs its `hasattr` keyword guard" rationale is replaced by the operative one — the mixin's
  attribute and methods must take precedence over any same-named member upstream may later
  add — and the docstring now says explicitly that mixin-first is *not* what satisfies the
  `as_view` guard, because that guard is a `hasattr` over the whole MRO. The already-correct
  trailing "a consumer subclass can override any part" clause is kept. The `#:` comment on
  `max_request_body_bytes` (`views.py #"rather than on each view"`) is **left alone**: it is
  about *where* the attribute is declared, is true, and stays coherent. (2) **Carried
  correction 1** — `_form_encoding_is_utf8`'s two numbered conditions are **re-ordered** so
  the numbering follows the body's evaluation order (declared `charset` first, matching
  `views.py:264-265`; effective encoding second, matching `:267`), the intro now reads
  "numbered in the order the body below evaluates them", and the internal cross-references
  were renumbered from "condition 1" to "condition 2" in the same edit. No code was reordered.
  The spec's *requirement* vocabulary for its three-part contract is untouched, so it still
  does not collide with this docstring's *condition* numbering.
- `tests/test_views.py` — **two** docstring edits, no assertion changed. (1) Module docstring
  first line `(spec-046 Slice 1)` -> `(spec-046 Slices 1-3)`, matching the file's actual scope
  (S1 import boundary, S2 cap rows, S3 wire rows) and the sibling
  `test_transport_api.py`; provenance kept, staging language absent. (2) **Carried
  correction 2** — `test_a_non_string_effective_encoding_is_refused_rather_than_escaping_as_a_typeerror`'s
  false justification ("A row asserting only `is False` would still pass while that happened.")
  is replaced by the true one: removing the `TypeError` arm makes the helper *raise* rather
  than return, so an `is False` row fails too; what the boundary assertion buys is that the
  assertions are the observable contract — the status code and the shared reason string —
  rather than a private helper's return value.
- `docs/README.md` — the section already on disk is finished:
  - three-wrapper corrections at all five pre-round-2 sites: the `## Today and coming next`
    router bullet, the new-`asgi.py` code comment, the `**CSRF.**` paragraph's WebSocket
    clause, the injected-consumer paragraph, and `## Session-auth deployment boundary`'s
    CSRF-absence sentence. `DjangoWebSocketHostValidator` now appears where it previously
    appeared zero times, always named as a **private** package validator, and the two
    "the router's origin defence is `AllowedHostsOriginValidator`, not a CSRF token"
    sentences now name **both** wrappers as two separate checks.
  - **Revocation** rewritten from the pre-round-2 single-checkpoint claim ("revalidates the
    session actor before every operation") to the Decision-16 contract: two checkpoints
    (admission + every information-bearing outbound operation frame), the exact "can neither
    admit another operation nor emit another information-bearing operation frame" claim,
    event-boundary-driven detection, whole-connection close with `4403` / `"Forbidden"` and no
    preceding operation error and no reconnect, and the window meaning the same thing at both
    checkpoints. The **idle-socket residue** is a stated paragraph of its own, named
    DoS-relevant and explicitly *not* an authorization hole, and it points at the existing
    connection-lifetime paragraph's knobs rather than duplicating them. That paragraph gained
    a `**Connection lifetime.**` bold lead-in so the pointer has a target; no heading was
    renamed, added, or re-nested anywhere in the section (sequencing constraint 4).
  - **WebSocket Host** — new paragraph carrying all four of Ruling 1's bullets: two separate
    checks, the `HttpRequest` projection + public `request.get_host()`, `ALLOWED_HOSTS` /
    `USE_X_FORWARDED_HOST` governing as they do on HTTP, **no new setting**, only
    `DisallowedHost` becoming a denial, and the denial preceding authentication and consumer
    construction.
  - **CSRF ordering** — new paragraph inside the `**CSRF.**` block that leads with "reads like
    a relaxation and is the opposite of one" and names it an **ordering mechanism, not a CSRF
    bypass** in its first sentence, before the word `csrf_exempt` is explained; it then gives
    the `csrf_protect` continuation and closes on the stricter-than-ordinary consequence (the
    endpoint stays CSRF-protected without the global middleware).
  - **Multipart control documents** — new paragraph: effectively-UTF-8 *and* survive Django's
    decode without a replacement marker, the `errors="replace"` mechanism that makes the
    second check necessary, both checks running before either value is parsed as JSON,
    `JSON.stringify` and genuine multibyte UTF-8 unaffected, the `\ufffd` escape named as the
    way to send a literal `U+FFFD`, and Django's parser / `request.POST` / `request.FILES` /
    upload handlers named as the sole owners of multipart parsing.
  - **Decision 8's second half** added to the multipart carve-out paragraph: the declaration
    *is* enforced before `MultiPartParser` and its upload handlers run, and that ordering is a
    property of the `csrf_exempt` / `csrf_protect` arrangement rather than of the cap.
  - The whole `## Transport…` + `### Transport deployment guidance` block was then re-read
    end to end. No further pre-round-2 residue: `grep` for `AllowedHostsOriginValidator`
    returns only sites that now name both wrappers or the code comment that now leads with the
    Host check, and "before every operation" is gone.
- `README.md` — `## Status`: the WebSocket-composition clause now carries the three-wrapper
  shape with `DjangoWebSocketHostValidator` named as private, and the two `-` separators the
  earlier partial hunk introduced were normalized to the file's em dashes. The paragraph still
  makes no claim the DRY table assigns elsewhere: no code recipe, no proxy directives, and it
  names `MAX_REQUEST_BODY_BYTES` / `413` without explaining them, cross-referencing
  `docs/README.md` through the existing `[readme]` def.
- `TODAY.md` — the single `**Channels ASGI router**` capability bullet, three-wrapper clause
  only. `git diff -- TODAY.md` before I started was exactly the two hunks CORRECTION 2
  predicted (the bullet + the `[readme-docs]` link def) and nothing else, so no concurrent
  work was present in that file; it is still two hunks now.
- `docs/SPECS/spec-041-channels_router-0_0_14.md` — the amendment banner immediately under the
  title and above the `Planned for 0.0.14` opening paragraph (which is **not** rewritten); it
  names exactly the three superseded items with working in-page anchors (each anchor copied
  from a link `spec-041` already carries, not hand-derived), states what survives unchanged,
  and states the `0.262.0` -> `0.316.0` reconciliation **as explicitly not a supersession**,
  per Decision 14. Plus `[spec-046]: ../spec-046-transport_security-0_0_15.md` added to the
  existing `<!-- docs/ -->` group, alphabetically between `[glossary]` and `[tree]`. Plus
  Ruling 5's six corrections and only those six: the 12 `0.262.0` mentions are now 6 corrected
  (the two pinned-floor claims, the three live-error-string descriptions, and the live test
  assertion) and 6 kept verbatim (the four explicitly-historical sentences and the two
  checklist / DoD rows recording what a past gate ran at). Checkbox state untouched.
  Pre-verified from source rather than from a document: `pyproject.toml:35` is
  `strawberry-graphql>=0.316.0` and `.github/workflows/django.yml:56` pins
  `strawberry: "0.316.0"` on the Django 5.2.0 / Python 3.10 node — the floor and the minimum
  CI node do agree, so there is no new Python 3.10 problem behind the reconciliation.
- `examples/fakeshop/test_query/README.md` — the raw-envelope exemption at the top is widened
  and now **says outright** that `test_transport_api.py` is made of nothing but raw-envelope
  subjects, enumerating the hostile-`Host` / `secure=` / `enforce_csrf_checks=` /
  `AsyncClient` rows, the in-process `ASGIHandler` driver, the real `multipart/form-data`
  control fields, and the `Client(enforce_csrf_checks=True)` ordering row with its
  upload-handler sentinel — rather than leaving a reader to infer it from the absence of a
  row. A new paragraph carries the **S1**, **S2** and **S9** acceptance rows, and
  `test_transport_api.py` was added to the sibling-suite enumeration that previously did not
  mention it. No migration recipe, no directives, no caps. The 10 link-def group headers and
  the file's narrative register are intact.
- `docs/TREE.md` — **regenerate only** (`scripts/build_tree_md.py`). New rows in **both** the
  current and target package layouts for `_request_body.py`, `consumers.py`, `views.py` and
  `utils/sessions.py` (CORRECTION 1 was right: all four were missing, `utils/sessions.py`
  included), a corrected `routers.py` row, and in **both** test-tree renderings new rows for
  `tests/test_views.py`, `tests/test_prove_failability.py` and
  `examples/fakeshop/test_query/test_transport_api.py` plus a corrected `tests/test_routers.py`
  row. No docstring was rejected.
- `docs/GLOSSARY.md` — **regenerate only** (`scripts/build_glossary_md.py`), 126 terms.
- `KANBAN.md`, `KANBAN.html` — **regenerate only**. `KANBAN.html`'s Vue shell was not touched;
  only its data block moved.
- `examples/fakeshop/db.sqlite3` — via the Django ORM only, never reset, applied on top. See
  `### Implementation notes` for the glossary and kanban writes.
- `docs/builder/bld-slice-5-docs_foldin.md` — this build report plus the checklist ticks.
- `docs/builder/worker-memory/worker-2.md` — consolidated, then one new entry.

**Baseline-dirty, untouched by me** (`AGENTS.md` L34, and the artifact's do-not-revert list):
`django_strawberry_framework/auth/mutations.py`, `auth/sessions.py`, `conf.py`,
the maintainer's incoming review, `docs/spec-046-transport_security-0_0_15.md`,
`docs/spec-046-transport_security-0_0_15-rationale.md` (never read),
`docs/builder/build-046-transport_security-0_0_15.md`,
`docs/builder/bld-review-2-w3_residual.md`, `drys.md`, `vulns.md`. Nothing was reverted.

#### Verify-only rows: each satisfies its bullet, quoted

Not authored this pass. The text is on disk from the maintainer's concurrent work; I read it
against the sub-check and made **no** edit.

| sub-check fragment | satisfying text on disk | verdict |
|---|---|---|
| `auth/sessions.py::classify_transport` unrecognized-scope message | `"Serve GraphQL over HTTP through DjangoGraphQLView in your URLconf, and over WebSocket through DjangoGraphQLProtocolRouter, so the scope carries a recognized protocol type."` | satisfied. It no longer tells the reader to route GraphQL HTTP through the router. |
| `auth/mutations.py::_login_resolve_body` / `::_logout_resolve_body` | both now read `"an async Channels consumer instead awaits the native async body"` and add `"Since spec-046 the package router serves no HTTP at all, so a Channels HTTP scope reaches here only from a consumer the project mounted itself."` | satisfied on both, identically worded. |
| `conf.py` `MAX_REQUEST_BODY_BYTES` multipart carve-out | `conf.py #"EXCEPT for a multipart request"` … `"so per-file count, per-file size, and aggregate size are NOT bounded by this key"`, and the Decision-8 co-requirement sentence is already there too (`#"is REQUIRED ALONGSIDE this one"`). | satisfied, both halves. |
| `tests/test_views.py` mixin-privacy trivially-true assertion dropped | `test_the_body_boundary_mixin_stays_private_and_sits_first_in_both_base_lists` carries exactly three assertions (`__bases__` twice, one MRO index), none about `__all__`, and its docstring records that privacy is proven once by the exact-`__all__` test. | satisfied. Its ordering rationale also already reads "must resolve to the package's implementation rather than to anything upstream might later define", i.e. it already agreed with the corrected `views.py` docstring. |
| `test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce` docstring | the `"the spec's Edge-case sentence predicting a 413 is inaccurate"` clause is gone; the `400` explanation and its `ASGIHandler.create_request` mechanism remain. | satisfied. |
| `test_transport_api.py` module docstring **first line** | `"""Live \`\`/graphql/\`\` transport-boundary acceptance tests (spec-046 Slices 1-3).` — and `git show HEAD:examples/fakeshop/test_query/test_transport_api.py \| head -1` prints the identical line, so it was already correct at `HEAD`. | satisfied; the Slice-3 sub-check's premise sentence is falsified, see `### Notes for Worker 1` item 1 (carried forward from the plan, re-verified this pass). |

**Phase A gate — observed.** Everything above this line landed, was lint-clean, and was
green under `uv run pytest tests/test_views.py --no-cov` (144 passed) before any DB write or
any regenerate ran.

### Tests added or updated

None, and none should be — the slice ships prose, generated docs and DB rows. The only `.py`
edits are docstring text; no assertion in any test file changed.

### Validation run

- `uv run ruff format django_strawberry_framework/views.py tests/test_views.py` -> pass,
  `2 files left unchanged`. Scoped, never `.`.
- `uv run ruff check --fix django_strawberry_framework/views.py tests/test_views.py` -> pass,
  `All checks passed!`.
- `uv run ruff format --check <same two>` / `uv run ruff check <same two>` (read-only re-check
  after Phase B) -> `2 files already formatted` / `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/views.py
  tests/test_views.py README.md TODAY.md docs/README.md docs/TREE.md docs/GLOSSARY.md
  KANBAN.md docs/SPECS/spec-041-channels_router-0_0_14.md
  examples/fakeshop/test_query/README.md` -> exit 0, no output. Explicit paths on every
  invocation; the tool was never run in its default repo-wide auto-fix mode, which is what
  keeps `drys.md` / `vulns.md` untouched.
- `git status --short` after both `ruff` invocations and again after the last regenerate ->
  every modified file is either on the artifact's writable list or on the declared
  baseline-dirty list. **No unexpected churn appeared**, so there was nothing to
  stop-and-report and nothing was reverted.
- `git diff --check` -> exit 0 (no whitespace errors, no conflict markers).
- `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues
  (0 silenced).`
- `uv run pytest tests/test_views.py --no-cov` -> **144 passed** (matches the declared
  baseline of 144).
- `uv run pytest tests/test_routers.py --no-cov` -> **122 passed** (matches the declared
  baseline of 122).
- `uv run pytest examples/fakeshop/apps/kanban examples/fakeshop/apps/glossary --no-cov` ->
  **167 passed**. The two apps whose rows changed; no model-level invariant broke.
- `uv run pytest examples/fakeshop/test_query/test_kanban_api.py
  examples/fakeshop/test_query/test_glossary_api.py --no-cov` -> **1 failed, 42 passed**:
  `test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard`. This is
  the **known subset-invocation artifact**, not a regression — it fails under a single-file /
  single-dir invocation and passes under the canonical full sweep (migration 0015). Confirmed
  rather than asserted:
- `uv run pytest --no-cov` (canonical full sweep) -> **5202 passed, 40 skipped in 91.15s**,
  exactly the declared baseline, that node included. No `--cov*` flag was used anywhere in
  this pass; `--no-cov` only.

#### Generated-doc verification: two consecutive regenerates, byte-compared

A clean `git diff` is not available on a slice that legitimately diverges the DB from `HEAD`,
so the proof is byte-stability across a second render, not a diff.

```
cp each of the four to scratchpad/pass1-*    # outside the repo
uv run python scripts/build_tree_md.py
uv run python scripts/build_glossary_md.py
uv run python scripts/build_kanban_md.py
uv run python scripts/build_kanban_html.py
cmp scratchpad/pass1-<f> <f>                 # per file
```

| file | second render | sha256 (first 16) |
|---|---|---|
| `docs/TREE.md` | STABLE (`cmp` exit 0) | `7bc4100d8893c011` |
| `docs/GLOSSARY.md` | STABLE (`cmp` exit 0) | `caa0e21daad6c53a` |
| `KANBAN.md` | STABLE (`cmp` exit 0) | `41e1741d6d0080a2` |
| `KANBAN.html` | STABLE (`cmp` exit 0) | `c0a4c12627c80d11` |

Worker 0's pre-edit baseline (`docs/GLOSSARY.md` and `KANBAN.md` regenerating byte-identically,
all four plus `db.sqlite3` clean in `git status`) held when I started, so every byte of churn
in those five files is this slice's.

Other gates the plan named:

- `uv run python scripts/build_tree_md.py --check` -> `docs/TREE.md is up to date.` (exit 0).
  It **failed** before this pass, as CORRECTION 1 recorded; that failure was this slice's work
  and is now closed.
- `uv run python examples/fakeshop/manage.py import_spec_terms` -> `Imported glossary terms
  for 46 done card(s).`; `… import_spec_terms --check` -> `OK: 46 done cards have glossary
  links.` (exit 0). Baseline was 45, expected 46, got 46.
- `uv run python scripts/check_spec_glossary.py --spec
  docs/spec-046-transport_security-0_0_15.md` -> `OK: 37 terms - all have glossary entries and
  at least one spec link.` (exit 0), run **after** the glossary regenerate, per sequencing
  constraint 7. No spec anchor was broken: no `GlossaryTerm.title` or `.anchor` was changed.
- `KANBAN.md`: `DONE-046-0.0.15` appears in `## Done` (and in the `## WIP / DONE spec map`),
  is **absent** from `## In progress` (which now holds only `TODO-ALPHA-050-0.0.19`), and its
  `#### Definition of done` renders boxes 0-4 as `- [x]` and box 5 as `- [ ]`.
- Version quintet / `CHANGELOG.md`: `git status --short` matches none of `pyproject.toml`,
  `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `CHANGELOG.md`.
  Nothing moved.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

Honoured as declared and not silently upgraded: nothing in this pass changes a code path. The
only `.py` edits are docstring text, evaluated once at import and never per request, per
resolver, per row, per connection, or per outbound message. The build plan's **build-wide**
hot-path declaration and its **M4** / **M5** escalations were not touched or re-litigated.

### Floor verification

Not applicable; plan declares floor-verification scope none.

Honoured as declared and not silently skipped: no floor venv was built, and the shared
`.venv` was **not** mutated — no `uv pip install` ran in this pass at all. For the record, and
read rather than recalled (`uv pip list`, plus `.venv/bin/python -V`): the shared environment
carries `django 6.0.5`, `strawberry-graphql 0.316.0`, `channels 4.3.2` on Python `3.14.2`,
which is the newest-supported set and **not** the floor. The canonical floor statement lives
in `docs/builder/BUILD.md` `## Floor verification`; this artifact does not restate it as a
fact of any environment.

### Implementation notes

- **The plan's `entry_order` monotonicity premise is FALSE as literally stated, and the
  mechanism it licenses still holds. Verified, not assumed.** Measured over all 119 rows:
  `entry_order` is **not** a dense sequence `5..N` and **not** monotone with `title_sort`.
  Three rows break it — `'django trac #37064 hardening'` sits at `77`, between `'testclient'`
  (76) and `'upload scalar'` (78), and two appendix entries sit at `1158`
  (`'cross-subsystem-invariants'`) and `1159` (`'auto-typed annotations'`), rendering after
  `## Visibility boundary` on purpose. `max(entry_order)` is 1159, not 79. **But** the
  alphabetical body — every `entry_order` from 5 to 79 except 77 — *is* monotone with
  `title_sort`, and all seven of this slice's alphabetical predecessors sit inside it. So the
  plan's predecessor-inheritance mechanism works unchanged, and I did **not** take the
  fallback re-rank: the 119 existing rows' `entry_order` / `index_order` are untouched, which
  is the minimal DB diff the plan wanted. Assignments, each = its alphabetical predecessor's
  pair: `connection-scoped-revocation` (11, 7), `djangographqlview` (19, 15),
  `request-body-cap` (64, 60), `utf-8-wire-contract` (78, 74), and the three
  `websocket-*` terms (79, 75).
- **Rendered positions read back after the regenerate**, as the plan required, in both the
  entry body and the generated `## Index` table. Every one is alphabetically correct:
  `Connection-scoped revocation` between `Connection-aware optimizer planning` and `Cookbook
  parity`; `` `DjangoGraphQLView` `` between `` `DjangoGraphQLProtocolRouter` `` and
  `` `DjangoImageType` ``; `Request-body cap` between `RELAY_GLOBALID_STRATEGY` and
  `` `request_from_info` ``; `UTF-8 wire contract` between `` `Upload` scalar `` and
  `Visibility boundary`; and the three `WebSocket …` entries after `Visibility boundary` and
  before the deliberate `Cross-subsystem invariants` / `` `auto`-typed annotations `` tail.
- **`status_text` for the seven new terms is the bare `shipped`, deliberately.** `0.0.15`
  would pre-empt the flip Decision 15 assigns to the joint cut (and the artifact's
  must-not-touch list names the `**Status:**` line of a glossary entry), and `0.0.14` would be
  false. Bare `shipped` is an established sibling shape — 9 existing entries use it — and it
  is exactly what the status legend defines as "implemented, tested, available in the current
  package surface". `status=shipped` in every case. Routed to Worker 1 as a deferral so the
  joint cut stamps the version; see `### Notes for Worker 1` item 9.
- **`GlossaryTermLink` rows do not render.** `build_glossary_md.py`'s `STATIC_GLOSSARY_QUERY`
  does not fetch them, so the visible "See also" line is prose inside `GlossaryTerm.body`. I
  wrote both: the prose (which is what a reader sees) and 23 `see-also` `GlossaryTermLink`
  rows for the seven new terms (which keep the relational model consistent with the prose,
  which is the glossary app's whole point). No existing term's links were touched — several
  shipped entries, `djangographqlprotocolrouter` included, carry See-also prose with zero link
  rows, and reconciling that backlog is not this slice's business.
- **Category membership `order` is curated, not alphabetical**, in every existing category, so
  the seven memberships were **appended** at `max(order) + 1` rather than inserted
  alphabetically: `integration-tooling` 27-31 for the five router/view-adjacent terms,
  `permissions` 11-12 for `websocket-host-boundary` and `connection-scoped-revocation` (which
  is where `channels-request-adapter` already sits). That respects the
  `(category, order)` unique constraint without renumbering anything.
- **The three glossary rewrites edited `body` only.** No `title`, no `anchor`, no
  `status_text`; `djangographqlprotocolrouter` still reads `shipped (\`0.0.14\`)`. The router
  entry's superseded composition, byte-compatible constructor, prefix-`^graphql` note and
  `strawberry-graphql>=0.262.0` hint are all replaced; `channels-request-adapter` is narrowed
  to WebSocket **reusing `auth/mutations.py`'s corrected wording** rather than inventing a
  second phrasing; `auth-mutations`' transport matrix now says the HTTP row is Django HTTP
  through the real `MIDDLEWARE` via `` `DjangoGraphQLView` ``.
- **The card flip went through `apps.kanban.services.set_card_status`**, not a bare
  `card.status = …; card.save()`, so the `CardTransition` is logged atomically and any
  unresolved incoming `blocked_by` edge is stamped. `actor="maintainer"` (the only `Actor`
  row); `note="spec-046 Slice 5: S12 transport doc fold-in, spec-041 amendment,
  GLOSSARY/TREE/KANBAN regenerated from source"`. `wip -> done`, `card_id` now
  `DONE-046-0.0.15`.
- **`SpecDoc` was verify-only, as the plan corrected.** Its `url` already read
  `https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-046-transport_security-0_0_15.md`;
  no write. `TrackedPath.objects.filter(card_links__card=card).count() == 0` re-confirmed, so
  the flip had no effect on `docs/TREE.md` and there was no flip-before-TREE ordering
  constraint — I regenerated `docs/TREE.md` first anyway, per the plan's step order.
- **`CardGlossaryTerm` bootstrap before the flip** (sequencing constraint 5), one row, on
  `djangographqlprotocolrouter` — an anchor that **is** in the 37-row CSV, so the later
  `import_spec_terms` reconciled it instead of deleting it.
- **`import_spec_terms` ran in write mode after the flip and before all three regenerates**
  (sequencing constraint 6). As the plan predicted, its `db.sqlite3` delta legitimately spans
  more than card 046 — it processes every `done` card and rebuilds `CardGlossaryTerm` +
  `GlossarySpecMention` from each card's CSV (the render reports 1408 spec mentions across 59
  specs). **Flagged, not narrowed, and not a defect.**
- **The terms CSV was not touched.** It stays at 37 rows and
  `check_spec_glossary.py` stays at `OK: 37 terms`, exactly as Ruling 3 decided; the seven new
  anchors are terms the card *authors*, not terms the spec *relies on*.
- `spec-041`'s banner uses in-page anchors **copied from links that file already contains**
  (`grep -on '(#decision-6…)'`), rather than hand-derived from the heading text, because the
  GitHub slug of a heading containing an em dash, backticks and `=` is easy to get wrong and a
  broken in-page anchor is silent.
- **Open reconciliation, raised and not resolved (fifth-plus consecutive pass):** all four
  role files tell a worker to scope its write-mode `ruff` runs to its own files, while
  `AGENTS.md:15` mandates the repo-wide `ruff format .` / `ruff check --fix .` and the role
  files defer to `AGENTS.md` on conflict. I used the scoped form the plan specifies and did
  **not** widen it — a repo-wide write-mode run would reformat the maintainer's concurrent
  `auth/`, `conf.py` and spec edits, and that churn is not mine to create or to revert. This
  needs a maintainer decision; recommended replacement line for `AGENTS.md:15`: *"Run
  `uv run ruff format` and `uv run ruff check --fix` after every edit, scoped to the files the
  change touched; the repo-wide `ruff format --check .` / `ruff check .` at the final gate
  stays read-only."*

### Notes for Worker 3

- The valuable review here is reading the finished prose against the shipped guard bodies, not
  against a sibling document. The load-bearing sources are `routers.py:437-438` (the
  window-plus-injected-consumer construction error) and `:449-461` (the three-wrapper
  composition and the `"http"` value), `consumers.py:1-56` (the two checkpoints, the seam, and
  what is deliberately not gated) and `:185-207` (`4403` / `"Forbidden"` /
  `_INFORMATION_BEARING_FRAME_TYPES`), `views.py`'s `_RequestBodyBoundaryMixin` docstring and
  `as_view`, `views.py::_form_encoding_is_utf8` (for the renumbering), and `conf.py:112-131`.
- Two prose claims worth checking hardest, because they are the ones a reader could be misled
  by: (a) the CSRF paragraph must not read as a relaxation anywhere in its first sentence, and
  (b) the idle-socket residue must be stated as DoS-relevant **and** as not an authorization
  hole, in that order.
- The seven new glossary bodies were written from the source modules and deliberately reuse
  the shipped docstrings' phrasing rather than inventing a second wording for the same
  contract; where a sentence looks lifted, that is why.
- No shadow file was generated or read this pass: the slice adds no Python logic, so
  `scripts/review_inspect.py`'s build-time triggers do not fire. Recorded as an explicit skip
  with that reason.
- The one focused-run failure in this report
  (`test_kanban_api.py::test_select_board_docs_and_lookup_roots_for_static_dashboard`) is the
  documented subset-invocation artifact and passes in the full sweep recorded above. Re-run at
  full scope, not at the two-file scope, if you want to confirm it.

### Notes for Worker 1 (spec reconciliation)

Items 1-8 were written by Worker 1 at plan time and are **not** repeated here; items 1, 4, 5,
6, 7 and 8 of that list were all re-verified as still accurate this pass, and item 1's premise
falsification was re-confirmed against `HEAD` (see the verify-only table). Items 2 and 3 are
now discharged in the direction the plan chose. What follows is **new**, from this pass.

9. **The seven new glossary entries carry `status_text = "shipped"` with no version, and the
   joint cut should stamp them.** Where it lives: `docs/GLOSSARY.md`'s seven new `##` entries
   (`DjangoGraphQLView`, `Request-body cap`, `UTF-8 wire contract`, `WebSocket
   consumer-injection seam`, `WebSocket Host boundary`, `WebSocket revalidation window`,
   `Connection-scoped revocation`) — DB-side, `GlossaryTerm.status_text`. Current wording:
   `**Status:** shipped.` Recommended replacement, **at the joint `0.0.15` cut and not
   before**: `**Status:** shipped (\`0.0.15\`).` Reason this slice could not write it: Decision
   15 gives the `0.0.15` status flip to the cut, and this artifact's must-not-touch list names
   the `**Status:**` line of a glossary entry explicitly. Route to `bld-final.md`'s
   `### Deferred work catalog` beside the `README.md` / `TODAY.md` "Coming next" -> "Shipped
   today" move, which has the same owner.
10. **`spec-041`'s own `Status:` line is stale and this slice had no authority to fix it.**
    Where it lives: `docs/SPECS/spec-041-channels_router-0_0_14.md`, the `Status:` line
    directly above the "Two slices (the card is a deliberate S)" paragraph. Current wording:
    `Status: **PLANNED — no slice built yet.**` That is factually wrong — card `041` is
    `DONE-041-0.0.14` and both its slices shipped. Recommended replacement:
    `Status: **SHIPPED (\`0.0.14\`). Amended by spec-046; see the banner above.**` I did not
    write it: Ruling 5 authorized the banner, the link def and the six `0.262.0` corrections
    and nothing else, and it explicitly says the Status line is left as the source of truth.
    This is a one-line custodian edit, not a builder edit.
11. **The Slice-5 sub-check's `docs/TREE.md` bullet undercounts the rows the regenerate
    added.** Where it lives: `docs/spec-046-transport_security-0_0_15.md`, `## Doc updates`,
    the `docs/TREE.md` bullet ("all four modules the earlier slices add … plus
    `tests/test_views.py` in the test trees"). The regenerate also published rows for
    `examples/fakeshop/test_query/test_transport_api.py` and `tests/test_prove_failability.py`,
    and corrected the `routers.py` and `tests/test_routers.py` rows. Recommended replacement
    for the bullet's tail: `… plus \`tests/test_views.py\`,
    \`examples/fakeshop/test_query/test_transport_api.py\` and
    \`tests/test_prove_failability.py\` in the test trees, and corrected \`routers.py\` /
    \`tests/test_routers.py\` rows.` Low stakes — the regenerate is source-driven and cannot
    omit a row — but the bullet reads as an exhaustive list and is not one.
12. **`docs/README.md`'s connection-lifetime paragraph gained a `**Connection lifetime.**`
    bold lead-in.** Where it lives: `docs/README.md`, `### Transport deployment guidance`, the
    paragraph beginning "The package does **not** impose a maximum connection lifetime". It is
    a bold lead-in inside a paragraph, **not** a markdown heading, so it creates no new anchor
    and breaks no `#transport-…` link (sequencing constraint 4 is intact). Flagged only
    because the spec's Doc-updates bullet enumerates the guidance paragraphs and this makes one
    of them separately addressable; no spec edit is required unless the custodian wants the
    enumeration to match.
13. **Nothing in this pass resolved, narrowed, or re-litigated `M4` or `M5`.** The slice-level
    `none` declarations for hot path and floor verification stand as the plan wrote them and
    are deliberately not evidence about the build-wide questions.


---

## Review (Worker 3)

Read the artifact's plan and build report, then the diff for every path in the subject list,
then `routers.py`, `consumers.py`, `views.py`, `_request_body.py` and `conf.py` **as the source
of truth**. Every claim below is graded against a shipped guard body or an executed command,
never against a sibling document or against the spec's prose.

**Cumulative-diff handling.** `git diff HEAD -- tests/test_views.py` carries the round-2
residual pass's whole new `test_a_non_string_effective_encoding_is_refused_rather_than_escaping_as_a_typeerror`
function, which was accepted uncommitted before this slice began. Slice 5's own contribution to
that file is exactly two docstring edits (the module first line and that row's justification
paragraph); the three `pytest.param` rows and the two assertions (`status_code == 400`,
`reason == _JSON_PARSE_REASON`) are byte-for-byte the shape the residual pass measured, so
**no assertion changed**.

### High:

None.

### Medium:

#### M1 — `routers.py`'s public constructor docstring still states the pre-round-2 revocation contract (pre-existing at HEAD; outside this slice's ownership)

`django_strawberry_framework/routers.py:405-407`, in `DjangoGraphQLProtocolRouter.__init__`'s
docstring — the text a consumer reads while choosing `websocket_revalidation_window=`:

```django_strawberry_framework/routers.py:405
        ``None`` (the default) selects the package's own
        ``consumers.py::GraphQLWebSocketConsumer``, which revalidates the session
        actor before every operation and rejects the operation - not the socket -
        when the session is no longer valid.
```

Decision 16 inverted both halves. The shipped contract is **two** checkpoints, and
`consumers.py #"Revocation is connection-scoped"` states the opposite of "not the socket":
"closes the whole socket with upstream's own ``4403`` / ``\"Forbidden\"``… the actor is
connection-scoped so the close IS the rejection". This is the same sentence Slice 5 just
corrected in `docs/README.md:360` and in the glossary — the contract is told in five places
(`consumers.py`'s module docstring, `docs/README.md`, the new `Connection-scoped revocation`
glossary entry, KANBAN card 046's scope, and here) and this is the one telling that drifted.

Pre-existing-at-HEAD, verified read-only:
`git show HEAD:django_strawberry_framework/routers.py | grep -n "before every operation and rejects the operation"`
prints `406:`, so the text is committed and was not introduced by this pass. `routers.py` is on
this slice's **must-not-touch** list, so closing it is an ownership decision, not a builder
choice — escalated below rather than held against this diff.

### Low:

#### L1 — a stray-comma typo this slice introduced into the rendered glossary

`docs/GLOSSARY.md` `## Channels request adapter` (source: `GlossaryTerm` id 529, `body`):

> …before reading `scope["type"]` to split a Channels HTTP scope from a WebSocket scope**,.** Since spec-046 the package router serves no HTTP at all…

At `HEAD` the sentence read "…from a WebSocket scope**, and** `login` / `logout` now run over
Channels HTTP…"; the rewrite replaced the tail and left the comma. New this pass, in a rendered
standing doc. Fix is one character in `GlossaryTerm.body` plus
`uv run python scripts/build_glossary_md.py` — a DB edit, never a hand-edit of the rendered file.

#### L2 — `README.md:62` puts `main`'s router shape inside the `0.0.14` description, then says what `046` removed

The paragraph opens `Newest shipped surface (`0.0.14`)` and now describes the WebSocket branch as
"the package's private `DjangoWebSocketHostValidator` (the `Host` check) over
`AllowedHostsOriginValidator` … while HTTP is dispatched straight to the consumer's own Django
ASGI application", and then adds "**Redesigned on `main` …**: … the Channels HTTP branch is
gone". Those two clauses contradict each other — if `0.0.14` already dispatched HTTP straight to
Django there was no Channels HTTP branch to remove — and the mis-attribution runs in the
direction that matters: it credits a **released** version with a `Host` check it does not have
(`DjangoWebSocketHostValidator` landed in round 2 of this card). The fix pattern already exists
in the two sibling surfaces, which lead with the marker instead of trailing it:
`docs/README.md:128` ("new in `0.0.14`, `DONE-041`; **redesigned on `main`** …") and
`TODAY.md:384`. Worker 1's `### Implementation steps` step 5 directed the in-place clause
replacement, so this is a plan-level choice, not a builder deviation.

#### L3 — the multipart carve-out is stated without its POST scoping (five surfaces, spec included)

`docs/README.md:360` — "For a `multipart/form-data` request the bound is the declared
`Content-Length` plus Django's own `MultiPartParser`, and nothing else" — and the new
`Request-body cap` glossary entry ("**`multipart/form-data` is a carve-out**: its bound is the
declared `Content-Length` …"). The carve-out is **POST-only**:

```django_strawberry_framework/views.py:290
    return request.method == "POST" and request.content_type == _MULTIPART_CONTENT_TYPE
```

so a multipart `Content-Type` on any other method skips the carve-out at
`views.py:516-519` and takes the **counted** `body_exceeds_limit` path. `views.py`'s own
`_is_multipart_form_post` docstring says so explicitly ("it is counted like any other body,
which is the stricter direction"), and spec **Decision 17** says "All three apply to precisely
the requests whose non-file fields Django decodes, which is a multipart **POST** and nothing
else". Direction: the docs *understate* enforcement, so nothing is exposed — but the sentence is
still not true as written. Note the ownership: **Decision 8 itself** uses the unscoped wording
("for a multipart request the bound is the declaration plus Django's `MultiPartParser`, not a
byte count"), and so do `conf.py #"EXCEPT for a multipart request"` and `views.py:407`
("**Multipart.** Bounded by the declared-size gate …"). Worker 2 reproduced the spec's own
words, so the fix is a one-clause harmonization across Decision 8 + those four surfaces, owned by
Worker 1 / the maintainer, not a Slice-5 re-loop.

#### L4 — the guidance's multipart pre-parse ordering claim is unconditional; the shipped source records the exception, and it is the deployment's own

`docs/README.md:360`: "an over-limit `Content-Length` on a multipart POST is refused with the same
`413`, with no part parsed, no file written, and no upload handler entered." True for the
ordinary stack. `views.py::_run_after_csrf_check` records the exception in bold:

```django_strawberry_framework/views.py:707
      **Any consumer middleware that touches ``request.POST`` (or ``request.body``) on the
      way in still runs before the view and therefore still beats the gate.**
```

The counted half of the same section *does* carry its honest boundary ("What it **cannot**
guarantee is that the bytes were never received…"), so the omission is asymmetric, and the party
who owns the caveat — a project with body-reading middleware — is exactly the reader of a section
titled `### Transport deployment guidance`. Not spec-required (Decision 8's Slice-5 obligation is
the carve-out plus the enforced-before-the-parser statement, both delivered), hence Low.
Recommended one clause, appended to that sentence: *"provided no project middleware reads
`request.POST` or `request.body` inbound — one that does runs before the view, and the cap can
then only refuse a body that was already materialized."*

#### L5 — `BACKLOG.md` still describes the router as serving HTTP (outside the spec's Doc-updates set)

`BACKLOG.md:1616`: "Transport substrate: **shipped** (spec-041, 0.0.14) —
`routers.py::DjangoGraphQLProtocolRouter` already wires Strawberry's Channels consumers onto
**HTTP + WebSocket** with `AuthMiddlewareStack` and origin validation …, so the WebSocket
endpoint subscriptions ride on exists today." Present tense, and false of live code on both
counts (no HTTP branch; the WebSocket branch has three wrappers). `:1661` carries the same shape.
`BACKLOG.md` is deliberately **not** in the spec's `## Doc updates` set, so this is a
maintainer/Worker-1 catalog item, not a gap in this slice.

#### L6 — Worker 1's Ruling 5 prose miscounts its own table

`### Ruling 5` says "a per-occurrence ruling on all **eleven** `0.262.0` mentions" and "**Six
corrections, five keeps**", while the table below it has **twelve** rows (6 CORRECT, 6 KEEP) and
`git show HEAD:docs/SPECS/spec-041-channels_router-0_0_14.md | grep -c "0\.262\.0"` prints
**12**. Worker 2 applied the table, reported "12 mentions … 6 corrected and 6 kept", and got it
right; the plan's prose is what is wrong. Recorded so the count is not re-derived a third time.

### DRY findings

This slice writes no Python logic, so there is no code duplication to weigh. The doc-surface
ownership table in `### DRY analysis` was **honoured**, verified by grep rather than by reading
the report:

- `grep -c client_max_body_size` → `docs/README.md` 1, `README.md` 0, `TODAY.md` 0,
  `docs/GLOSSARY.md` 0. The concrete proxy/ASGI directives live at exactly one site.
- `README.md:62` / `TODAY.md:384` stay prose-only: they name `MAX_REQUEST_BODY_BYTES` / `413`
  without explaining them, carry no code block and no directive, and cross-reference
  `docs/README.md` through the existing `[readme]` / `[readme-docs]` defs.
- The new `Request-body cap` glossary entry **points** rather than copies ("`docs/README.md`
  carries the concrete directives plus the reason none of Uvicorn, Hypercorn, or Daphne supplies
  one"), which is the right shape for a self-contained entry.
- `examples/fakeshop/test_query/README.md` and `spec-041`'s banner restate no recipe, no
  directive and no cap.

The only DRY defect found is **M1**: a contract told in five places, one of which drifted. That is
the failure mode this table exists to prevent, and it landed in the one file the slice was
forbidden to touch.

**Existence challenge:** none raised. The slice introduces no helper, registry, indirection or
token; the four render scripts are pre-existing and are the only writers of the generated docs.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the
re-export list are unchanged. No new public export. `django_strawberry_framework/views.py`'s
diff is docstring text only (no `__all__` line in it changed), so the private
`_RequestBodyBoundaryMixin` stays private.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. Verified, not assumed:
`git diff HEAD --stat -- CHANGELOG.md` is empty and `CHANGELOG.md` is absent from
`git status --short`.

**Version quintet:** `pyproject.toml` (`version = "0.0.14"`),
`django_strawberry_framework/__init__.py` (`__version__ = "0.0.14"`),
`tests/base/test_init.py` (`assert __version__ == "0.0.14"`) and `CHANGELOG.md` all show an
empty `git diff HEAD --stat` and none appears in `git status --short`. Untouched, per
Decision 15.

### Documentation / release sanity

**Generated docs — my own byte-stability proof, not the builder's.** Snapshotted all four plus
`examples/fakeshop/db.sqlite3` outside the repo, then ran each render **twice** and `cmp`'d each
pass against the snapshot. The pre-run digests matched the build report's four prefixes exactly,
so the tree was in the state the builder recorded.

| file | sha256 (pre) | after regenerate #1 | after regenerate #2 |
|---|---|---|---|
| `docs/TREE.md` | `7bc4100d8893c011…` | `cmp` exit 0 | `cmp` exit 0, digest unchanged |
| `docs/GLOSSARY.md` | `caa0e21daad6c53a…` | `cmp` exit 0 | `cmp` exit 0, digest unchanged |
| `KANBAN.md` | `41e1741d6d0080a2…` | `cmp` exit 0 | `cmp` exit 0, digest unchanged |
| `KANBAN.html` | `c0a4c12627c80d11…` | `cmp` exit 0 | `cmp` exit 0, digest unchanged |
| `examples/fakeshop/db.sqlite3` | `9b9d4b4aacaf1d85…` | unchanged | unchanged |

Because the on-disk bytes equal the render output, **no hand-edit survives in any of the four** —
which is the property a `git diff` cannot establish. The DB was never reset; the renders do not
write to it.

**Glossary seeding — verified against `HEAD`'s own database.** Extracted `HEAD`'s
`db.sqlite3` to a scratch path outside the repo (`git show HEAD:…`, read-only) and diffed
`(id, anchor, title, entry_order, index_order, title_sort)` for all rows:

- **Zero** rows present at `HEAD` differ in any of those columns. No existing row was re-ranked,
  and **no `GlossaryTerm.title` or `.anchor` changed** — so no `GLOSSARY.md#anchor` link in the
  repo can have broken. Exactly seven rows are new, with the predecessor-inherited pairs the
  build report lists (`connection-scoped-revocation` 11/7, `djangographqlview` 19/15,
  `request-body-cap` 64/60, `utf-8-wire-contract` 78/74, the three `websocket-*` 79/75).
- Diffing `(status_text, status_id, length(body))` shows exactly **three** existing bodies
  changed — ids 441 `auth-mutations`, 453 `djangographqlprotocolrouter`, 529
  `channels-request-adapter` — with `status_text` untouched on every existing row
  (`djangographqlprotocolrouter` still `shipped (`0.0.14`)`), and the seven new rows at bare
  `shipped`. That is Ruling 3 exactly.
- The premise the plan doubted is safe for a reason worth recording: **both** renderings sort by
  a tuple, `scripts/build_glossary_md.py #"(value[\"indexOrder\"], value[\"titleSort\"])"` for the
  `## Index` and `#"(value[\"entryOrder\"], value[\"titleSort\"])"` for the entry bodies, so the
  deliberate `entry_order` ties break alphabetically and are deterministic.
- Rendered positions read back myself, in both places. Entry bodies:
  `Connection-scoped revocation` between `Connection-aware optimizer planning` and `Cookbook
  parity`; `` `DjangoGraphQLView` `` between `` `DjangoGraphQLProtocolRouter` `` and
  `` `DjangoImageType` ``; `Request-body cap` between `RELAY_GLOBALID_STRATEGY` and
  `` `request_from_info` ``; `UTF-8 wire contract` between `` `Upload` scalar `` and `Visibility
  boundary`; the three `WebSocket …` after `Visibility boundary` and before the deliberate
  `Cross-subsystem invariants` tail. The `## Index` table lists the same seven in the same
  neighbours. All alphabetically correct.

**Card wrap.**

- `uv run python examples/fakeshop/manage.py import_spec_terms --check` →
  `OK: 46 done cards have glossary links.` (exit 0). Baseline 45, so +1 for card 046.
- `KANBAN.md`: `DONE-046-0.0.15` appears once under `## Done` (`:1340`) and once in the
  `## WIP / DONE spec map` (`:98`); `## In progress` holds only `TODO-ALPHA-050-0.0.19`. Rendered
  `#### Definition of done` boxes 0-4 are `- [x]`, box 5 `- [ ]`, per Ruling 4.
- The three card-text corrections landed and read correctly against the shipped contract: `scope`
  S11 now says two checkpoints + connection-scoped close, `definition_of_done` order 3 the same,
  `arch_posture` order 3 the three-wrapper composition with the Host validator outermost.
- **The "wider than card 046" DB delta is narrower than the build report feared, and I measured
  it rather than accepting the flag.** Row-count deltas vs `HEAD`: `glossaryterm` +7,
  `glossarycategorymembership` +7, `glossarytermlink` +23, `glossaryspecmention` +37,
  `cardglossaryterm` +37, `cardtransition` +1, `uuidmodel` +38. Identity diffs: the 37 new
  `GlossarySpecMention` rows are **all** `spec_path = docs/spec-046-transport_security-0_0_15.md`
  with **zero** removals; the 37 new `CardGlossaryTerm` rows are **all** `card_id = 65` (orders
  0-36) with **zero** rows removed or re-ordered for any other card; all 23 new
  `GlossaryTermLink` rows are sourced from the seven new terms; the 7 new memberships are
  appended at `max(order)+1` in categories 104 and 99. So write-mode `import_spec_terms` perturbed
  no other done card at all — the byte-level churn is SQLite page movement, not semantic reach.
  This is the documented reconciliation, not something else.
- `CardTransition` id 5: card 65, `wip → done`, `actor=maintainer`, note
  `"spec-046 Slice 5: S12 transport doc fold-in, spec-041 amendment, GLOSSARY/TREE/KANBAN
  regenerated from source"`. Went through the sanctioned service, as Ruling 4 required.

**`spec-041`.** Banner sits above the untouched `Planned for 0.0.14` opener, names exactly the
three superseded items with in-page anchors, and states the floor reconciliation as explicitly
*not* a supersession. `0.262.0` occurrences: **12 at `HEAD` → 8 now**, and the four that
disappeared plus the two rewritten-in-place are exactly the six lines Ruling 5's table marked
CORRECT (24, 339, 927, 1148, 1258, 1868); the five it marked KEEP (173, 265, 498, 672, 1260) plus
2048 are verbatim. Two of the eight remaining are the banner's own quotations. **Checkbox state
is byte-identical**: `diff` of every `- [ ]` / `- [x]` line between `git show HEAD:` and the
working copy is empty (11 indented + 22 top-level, all unticked, both sides).

**Markdown links.** Every in-page anchor in `docs/README.md` resolves to an existing heading (3
refs, 0 missing, checked by slugifying every heading in the file); no heading in the transport
section was renamed, added or re-nested, so
`#transport-the-graphql-http-endpoint-and-the-asgi-router` (used twice in `docs/README.md`)
still lands. `README.md` / `TODAY.md` link `docs/README.md` through their existing defs with no
fragment, so nothing there can break. `spec-041`'s new `[spec-046]` def resolves to a real file.
`scripts/check_trailing_commas.py --check` with explicit paths over all ten changed
`.py` / `.md` files → exit 0, so the 10-group link-def scaffold is intact everywhere.

**Staging-vs-provenance.** The regenerate published
`tests/test_views.py  # Package-tier contracts … (spec-046 Slices 1-3).` and
`test_transport_api.py  # Live ``/graphql/`` transport-boundary acceptance tests (spec-046 Slices
1-3).` A naive reading of the "no `Slice N`" rule would flag both. They are **provenance**, not
staging: they name which slices' contracts the file covers, contain no "planned" / "after Slice
N" / `TODO(`, and the `test_transport_api.py` spelling was already at `HEAD`. Correct as shipped.

**Verbatim-copy check.** Nothing in this slice is a character-for-character drop-in from the spec
— the card-item corrections, the glossary bodies and the guidance paragraphs were authored from
the source modules (which the plan's `### Implementation discretion items` licensed), so the
`diff`-against-the-spec obligation does not apply. Spot-checked that the glossary bodies do not
silently diverge from the modules they paraphrase; they do not.

**Obsolete-wording sweep.** `docs/README.md`'s new capability bullets sit under `**Shipped
today** (`0.0.14`)` but are marked "**new on `main`**" / "**redesigned on `main`**" inline, which
is the convention that file already uses ("as of the visibility-boundary hardening on `main`").
The `shipped (0.0.15)` flip and the "Coming next" → "Shipped today" move are Decision 15's, and
were correctly left alone. `README.md:62`'s variant of the same marker is L2 above.

### Migration-note verification — it executes

`BUILD.md`'s point that a migration note which does not run is worse than none deserved an
executed answer rather than a read one, so I wrote a probe that runs the note's own code
verbatim (`docs/builder/temp-tests/slice-5-w3/test_migration_note_executes.py`, **8 passed**):

- the documented **new `asgi.py`** call — `DjangoGraphQLProtocolRouter(schema, django_asgi_app,
  websocket_url_pattern=r"^graphql/?$")` — constructs, `application_mapping["http"] **is**` the
  Django ASGI application by identity, and the WebSocket value is
  `DjangoWebSocketHostValidator` → `OriginValidator` → (`AuthMiddlewareStack` chain) →
  `URLRouter`, i.e. the three wrappers in the documented order;
- the documented **`urlpatterns` entry** — `path("graphql/",
  DjangoGraphQLView.as_view(schema=schema))` — builds, and so does the `AsyncDjangoGraphQLView`
  twin "mounted identically";
- migration-table row 1: omitting `django_application` raises `TypeError`; `None` / `"str"` / `3`
  each raise `ConfigurationError` whose message names both halves of the migration
  (`django_application=…get_asgi_application()` **and** the `DjangoGraphQLView` URLconf entry) —
  so "whose message names this migration" is true, not aspirational;
- migration-table row 2: the old `url_pattern=` keyword is now a `TypeError`, and
  `r"^graphql/?$"` matches `graphql` / `graphql/` while rejecting `graphql-admin`,
  `graphqlanything` and `graphql/extra` — the three spellings the table names.

One incidental correction to the reviewer's own first assertion, recorded so a later pass does
not repeat it: `AllowedHostsOriginValidator` is a **factory function**, not a class, so the
composition must be asserted against `channels.security.websocket.OriginValidator`. The docs'
naming is fine (it is how `routers.py` and `spec-041` both spell it).

### Deployment-knob claims, verified against the installed packages rather than recalled

Every Daphne knob the guidance names exists with the stated shape:
`daphne/server.py:55 request_buffer_size=8192` and **no** `request_buffer_size` in
`daphne/cli.py` (so "a `daphne.server.Server` keyword, default `8192`, with no CLI flag" is
exact); `--websocket_timeout`, `--websocket_connect_timeout`, `--websocket-max-message-size` and
`--websocket-max-frame-size` are all real `cli.py` arguments. The "upstream's own RFC 8259
auto-detection" attribution for plain `strawberry.django.views.GraphQLView` is the package's own
recorded contract (`_cross_web_patches.py #"RFC 8259"`, spec `:1271`, and a live row at `:2553`
pinning the `200`), so it is not a new claim. Uvicorn is not installed in this environment, so
`--h11-max-incomplete-event-size` was not executed — it is a header-shaped knob claim in the
direction that concedes rather than promises, and it is the spec's own statement.

### Failability proofs

Audited: the diff introduces **no** new boundary, guard, gate, rejection path or validation
branch, so the build report's `None; this pass introduced no new boundary.` is correct, and the
mandatory re-run floor is satisfied by an **empty** re-run set — legal precisely because nothing
in the diff meets it. Verified by reading rather than accepting: `git diff HEAD --` over the two
`.py` files touches only docstring lines (`views.py` hunks at `:225-249` and `:366-376`;
`tests/test_views.py` the module first line and one docstring paragraph), and the executable
addition in `tests/test_views.py`'s cumulative diff belongs to the already-accepted round-2
residual pass, whose 3-row node-id set I measured myself in that pass.

### Hot-path budget

Honoured as declared (`none`). Confirmed independently: no executable line changed anywhere in
the diff, so nothing runs per request, per resolver, per row, per connection or per outbound
message that did not run before. The build-wide **M5** number and **M4** were not touched by this
pass and are not touched by this review.

### Floor verification

Honoured as declared (`none`). Confirmed independently: the slice touches no Django / Strawberry
/ channels integration seam — its `.py` delta is docstring text, and everything else is Markdown,
the kanban/glossary DB, and four scripts outside the package. No floor venv was built by this
review and **no `uv pip install` ran**, so the shared `.venv` is unmutated. The canonical floor
statement is `BUILD.md` `## Floor verification`; this section deliberately restates no version as
a fact of any environment.

### Static helper use

`scripts/review_inspect.py` **skipped**, reason recorded per `worker-3.md`: the slice adds no
Python logic, so there is no control flow to read in a shadow file and no repeated-literal or
import-boundary evidence a DRY finding here would rest on. The repeated-literal question was
answered directly by grep over the six doc surfaces (see `### DRY findings`). No shadow file was
generated or read.

### Gates re-run by this review

- `uv run pytest --no-cov` → **5202 passed, 40 skipped** (exit 0). Exactly the declared baseline.
- `uv run pytest docs/builder/temp-tests/slice-5-w3/… --no-cov` → 8 passed (the probe above).
- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0 silenced).`
- `uv run python scripts/build_tree_md.py --check` → `docs/TREE.md is up to date.` (exit 0). It
  failed before this slice, as CORRECTION 1 recorded; that failure is closed.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md`
  → `OK: 37 terms - all have glossary entries and at least one spec link.` (exit 0), run after
  the regenerates. No anchor broken.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 46 …` (exit 0).
- `uv run ruff format --check` / `uv run ruff check`, read-only, on the two `.py` files →
  `2 files already formatted` / `All checks passed!`. No write-mode `ruff` ran in this review.
- `uv run python scripts/check_trailing_commas.py --check <ten explicit paths>` → exit 0. The
  tool was never invoked without paths, so `drys.md` / `vulns.md` were never reachable.
- Both `.py` files contain **0** non-ASCII bytes.
- **Pre-commit hazard checked** (`BUILD.md`'s gate does not run the hooks): the
  `kanban-tracked-path-constants` hook is a no-op here — I snapshotted
  `examples/fakeshop/apps/kanban/constants.py`, re-ran
  `scripts/build_kanban_tracked_path_constants.py`, and `cmp` is byte-identical, so the DB writes
  cannot trigger the stash-conflict rollback that has bitten this repo before.
- **Independent staleness sweep** (run against my own grep, never the slice's file list): grepped
  the whole test tree plus `scripts/` for `docs/README|GLOSSARY.md|TREE.md|KANBAN.md|spec-041|
  test_query/README`; every hit is a docstring reference or a render script, none an assertion on
  the changed prose, and the full sweep is green — including the kanban/glossary app tiers whose
  rows moved.
- `git status --short` at the end is **identical** to the start (19 `M` + 4 `??`), plus nothing:
  my only writes are this artifact section, `worker-memory/worker-3.md`, and the gitignored
  `docs/builder/temp-tests/slice-5-w3/`.

### What looks solid

- **The seven-place three-wrapper sweep is complete and correct.** All seven pre-round-2 sites
  from the carried list (`docs/README.md:128`, `:283`, `:316`/`:320`, `:390`/`:402`,
  `:398`/`:410`, `README.md:62`, `TODAY.md:384`) now name `DjangoWebSocketHostValidator`, and I
  found no eighth: a repo-wide `--include="*.md"` grep for `AuthMiddlewareStack` outside
  `docs/builder`, `docs/SPECS`, `docs/review`, `docs/dry` and `docs/bug_hunt` leaves only
  `CHANGELOG.md:24` (a `0.0.14` release record the card may not touch), `KANBAN.md:1415`/`:1421`
  (the card body, correct and historical) and `BACKLOG.md` (L5). Both "the router's origin defence
  is `AllowedHostsOriginValidator`, not a CSRF token" sentences now name **both** wrappers as two
  separate checks, which is the maintainer's decided contract and the rejected round-2 finding-4
  claim's opposite.
- **The revocation paragraph is exactly right — neither over- nor under-claiming.** It carries
  Decision 16's literal claim ("a revoked actor can neither admit another operation nor emit
  another information-bearing operation frame"), the correct frame set (`next` / `data` /
  operation-scoped `error`, matching `consumers.py`'s `_INFORMATION_BEARING_FRAME_TYPES`), the
  correct admission entry points, `4403` / `"Forbidden"` as *upstream's own* code and reason
  (`consumers.py:185-198`), whole-connection close with no preceding operation error, the window
  meaning the same thing at both checkpoints, and the idle-socket residue **stated** as
  DoS-relevant and **explicitly not** an authorization hole, in that order. The pre-round-2
  "before every operation" understatement is gone from every doc surface.
- The **WebSocket Host** paragraph's every clause traces: the `HttpRequest` projection and public
  `get_host()` (`consumers.py::_host_validation_request`), `USE_X_FORWARDED_HOST` genuinely
  governing (`_HOST_META_KEYS_BY_HEADER` projects `x-forwarded-host` and lets Django pick),
  `DisallowedHost` as the only denial with everything else propagating, and the denial preceding
  authentication and consumer construction because the validator is outermost.
- The **CSRF ordering** paragraph leads with "reads like a relaxation and is the opposite of one"
  and names it an ordering mechanism before `csrf_exempt` is explained, so the skim-misreading
  the spec warned about cannot happen; the stricter-than-ordinary consequence matches
  `views.py:692-694` exactly.
- The **multipart control-document** paragraph is accurate down to the mechanism: the
  `errors="replace"` decode, the marker check running before `json.loads`, and the six-character
  ASCII JSON escape being the supported way to carry a literal `U+FFFD` (which
  `_reject_lossy_multipart_control_fields` allows because it inspects the *serialized* value).
- **Decision 8's co-requirement is named where a reader of the proxy-cap paragraph alone would
  need it** — the multipart carve-out sentence is in that same paragraph block, and the
  "co-requirement of the application cap, never an alternative to it" wording is verbatim the
  decision's posture.
- **Carried correction 1 is right, including its cross-reference.** The docstring's conditions are
  now numbered in the body's evaluation order — declared `charset` first
  (`views.py:264-265`), effective encoding second (`:267`) — the intro says so, and the internal
  reference was renumbered in the same edit ("Not implied by condition **2**"). No code moved.
  The spec's *requirement* vocabulary is undisturbed: `grep` finds exactly one numbered
  cross-reference in the spec (`:1926` "Requirement 1"), inside Decision 17, whose three
  **requirements** are a different vocabulary over a different set. Worth stating for a future
  reader, since spec requirement 1 (effective encoding) and docstring condition 1 (declared
  `charset`) are now inverted — they do not collide, but they are not parallel either.
- **Carried correction 2 is right and provable.** The false clause is gone and the replacement is
  the true one — removing the `TypeError` arm makes the helper *raise*, so an `is False` row
  fails too — which is exactly what the round-2 residual pass proved by mutation. Assertions
  untouched.
- Every verify-only row re-read against source by me, not relayed: `auth/sessions.py:127-128`
  now routes HTTP through `DjangoGraphQLView`; both `auth/mutations.py` docstrings
  (`:595`, `:778`) carry the identical "no HTTP at all" sentence; `conf.py`'s
  `MAX_REQUEST_BODY_BYTES` comment carries both the carve-out and the
  `#"is REQUIRED ALONGSIDE this one"` co-requirement; the mixin-privacy test has three
  assertions and none about `__all__`; `test_transport_api.py`'s first line is
  `(spec-046 Slices 1-3)` and its `413` clause count is `0`.
- The `Request-body cap`, `UTF-8 wire contract`, `WebSocket revalidation window`,
  `WebSocket consumer-injection seam`, `WebSocket Host boundary`, `Connection-scoped revocation`
  and `` `DjangoGraphQLView` `` entries all cite the right Decision numbers (6, 7, 9+10, 11+16,
  17, 19) and every load-bearing sentence in them traces to a shipped body — including the
  `None`-in-the-setting versus `None`-as-the-keyword distinction (`views.py:456-459`) and the
  `400`-versus-`413` ceiling discrimination.

### Temp test verification

- `docs/builder/temp-tests/slice-5-w3/test_migration_note_executes.py` — 8 rows, all passing;
  fresh subdirectory, gitignored, never reused from an earlier cycle.
- **Disposition: no promotion needed, and I checked rather than assumed.** The probe caught no
  bug, and the permanent suite already pins the same claims — `tests/test_routers.py:458` asserts
  the outermost wrapper is `DjangoWebSocketHostValidator` and `:1650-1652` parametrizes
  `/graphql-admin` / `/graphqlanything` / `/graphql/extra` as non-matches. The probe's only
  unique contribution is executing the note's literal text, which is a review act, not a
  standing contract.

### Notes for Worker 1 (spec reconciliation)

The build report's items 9-13 are all sound and I add nothing to them; item 10 (`spec-041`'s
`Status:` line still reading `PLANNED — no slice built yet`) is independently confirmed and is
the highest-value one-line custodian edit in this set.

1. **Escalated: M1 — `routers.py:405-407`'s constructor docstring still states "rejects the
   operation - not the socket".** Pre-existing at `HEAD`, in a file this slice was forbidden to
   touch, and it is the last surviving pre-round-2 telling of the revocation contract on a
   **public** constructor. Resolution paths, in the order I would take them: (a) fold it into the
   cross-slice integration pass, which already owns two `test_transport_api.py` items and can
   edit `routers.py` under a declared partition; (b) a one-paragraph Worker-2 re-loop scoped to
   that docstring alone; (c) route to the maintainer with the joint `0.0.15` cut, accepting that
   `0.0.15` would ship the wrong sentence on a public API. I recommend (a). It is not grounds to
   hold this slice: nothing in Slice 5's diff caused it, and Slice 5 fixed the other four
   tellings.
2. **L3 belongs to the spec, not the builder.** Decision 8's own carve-out sentence omits the
   POST scoping that Decision 17 states explicitly, and `conf.py` / `views.py:407` inherited the
   omission before this slice existed. One clause ("on a multipart **POST** — the carve-out is
   POST-scoped, and a multipart content type on any other method is counted like any other body")
   harmonizes Decision 8, `conf.py`, `views.py:407`, `docs/README.md:360` and the new
   `Request-body cap` entry. Two of those five are production source, so this is a
   maintainer-sequenced edit, not a doc-slice one.
3. **L4's one clause is a judgement call worth the custodian's eye,** because adding it makes the
   deployment guidance longer and slightly less quotable in exchange for being true under a
   body-reading middleware. Decision 8 does not require it; `views.py::_run_after_csrf_check`
   already carries it for a code reader. Paths: (a) add the clause to `docs/README.md:360`;
   (b) add a Decision-8 sentence and let the doc inherit it; (c) reject and record that the code
   docstring is the authoritative statement of the exception.
4. **Decision 8's list of "concrete directions" names a knob that does not bound the body.** It
   says "`--limit-request-field-size` / equivalents on the ASGI server"; the shipped guidance
   correctly explains that Gunicorn's `--limit-request-line` / `--limit-request-field_size` and
   Uvicorn's `--h11-max-incomplete-event-size` bound the request line and headers, **not** the
   body, and that none of Uvicorn / Hypercorn / Daphne ships a total-body limit. The doc is
   better than the decision here; worth reconciling so a future reader does not "restore" the
   spec's weaker direction.
5. **L6 — Ruling 5's prose says eleven mentions / five keeps where its own table says twelve /
   six**, and `HEAD` had twelve. Worker 2 followed the table and was right.
6. **L2's framing decision is Worker 1's**, since `### Implementation steps` step 5 directed the
   in-place clause replacement in `README.md`'s `0.0.14` sentence. Either lead with the marker
   (the shape `docs/README.md:128` and `TODAY.md:384` already use) or restore the `0.0.14`
   description and let the "Redesigned on `main`" sentence carry the new shape.
7. **L5 — `BACKLOG.md:1616` / `:1661`** describe the router as serving HTTP + WebSocket in the
   present tense. Deliberately outside the spec's Doc-updates set, so it is a
   `### Deferred work catalog` entry, not a gap.
8. **Recorded so a later pass does not "fix" it:** KANBAN card 046's `arch_posture`
   injection-seam bullet still says "Per-operation session revalidation is a WebSocket concern
   layered through that seam". Ruling 4 scoped card-text corrections to exactly three items and
   kept the RECOMMENDED-DIRECTION framing and all three `open_question` items as historical
   record. That is a deliberate choice, and it is right.
9. **The plan's own `### Notes for Worker 1` item 3 (the CSV deliberately left at 37 rows) is
   sound and I endorse it.** `check_spec_glossary.py` gates *every* CSV row against a spec link,
   so growing the CSV without the matching spec edit would leave the gate red between two passes.
   The seven authored terms genuinely are terms the card *authors* rather than terms the spec
   *relies on*.

### Review outcome

`review-accepted`.

No High findings. One Medium (**M1**) is transparently escalated to Worker 1 above with ordered
resolution paths, per `worker-3.md`'s escalation clause: the defect is pre-existing at `HEAD`, in
a file on this slice's must-not-touch list, so resolving it is an **ownership** decision Worker 2
cannot make. The six Low findings are recorded with their dispositions — L1 is the only one this
slice introduced, and it is a one-character DB fix plus a regenerate; L3, L4, L5 and L6 are
Worker-1 / maintainer items by ownership rather than builder omissions, and L2's framing was the
plan's instruction. Every generated doc is byte-stable across two consecutive regenerates that I
ran myself, no `GlossaryTerm.title` / `.anchor` moved, no existing glossary row was re-ranked, the
card wrap is correct at `OK: 46`, the version quintet and `CHANGELOG.md` are untouched, both
carried prose corrections are right, and the migration note **executes as written**.

---

## Final verification (Worker 1)

Read the whole artifact (plan, build report, Worker 3's review), then re-derived every claim
below from the tree rather than from any pass's prose. Nothing in this section rewrites another
worker's text; the one correction to a prior section is appended under
`### Correction appended to Worker 3's L6`, per the no-rewrite rule.

### Spec slice checklist audit — all ten sub-checks, one at a time

Every box was `- [x]` when I arrived; **every tick is upheld and none was added or removed.**
Nothing is left `- [ ]`, so no deferral line is owed for the checklist itself.

| sub-check | verdict | evidence I re-derived |
|---|---|---|
| migration note (old vs new `asgi.py` + `urlpatterns`) | **landed** | `docs/README.md:252` / `:275` carry the two `get_asgi_application()` blocks, `:291-301` the `urlpatterns` entry under "**The `urlpatterns` entry the new `asgi.py` depends on**", `:310` the `APPEND_SLASH` policy including the `301`-is-not-re-POSTed warning, `:241` the three-row breaking-change table. |
| transport deployment guidance | **landed** | `client_max_body_size 1m` at `:348`, `LimitRequestBody 1048576` at `:355`, the Daphne `request_buffer_size` note at `:358`, the multipart carve-out at `:360`. `grep -c` over `docs/README.md`: `csrf_exempt` 2, `csrf_protect` 2, `U+FFFD` 1, `get_host` 1, `USE_X_FORWARDED_HOST` 1, `4403` 1, `DjangoWebSocketHostValidator` 5 — all four mechanism paragraphs present and each naming its mechanism, not a family. `before every operation` is **0** in `docs/README.md`, `README.md` and `TODAY.md`. |
| `spec-041` banner + floor reconciliation | **landed** | banner at `:3-38`, above the untouched `Planned for 0.0.14` opener, naming exactly the three superseded items and stating the floor reconciliation as explicitly not a supersession. `0.262.0`: **12 at `HEAD` -> 8 now**; I re-ran the count both sides myself. Checkbox state byte-identical. |
| `docs/GLOSSARY.md` + `docs/TREE.md` + `README.md` / `TODAY.md` | **landed** | TREE rows for all four modules in **both** layouts (`_request_body.py` `:196`/`:310`, `consumers.py` `:201`/`:315`, `views.py` `:213`/`:326`, `utils/sessions.py` `:293`/`:409`) plus `tests/test_views.py` `:457`/`:669`; `build_tree_md.py --check` exits 0 where it failed before the slice. `docs/GLOSSARY.md` carries all seven new `##` entries (`:370`, `:536`, `:1476`, `:1800`, `:1820`, `:1830`, `:1840`). `README.md:62` and `TODAY.md:384` both name `DjangoWebSocketHostValidator`. |
| the three `auth/` transport strings | **landed, legitimately verify-only** | The corrected text is on disk in `auth/sessions.py::classify_transport` and both `auth/mutations.py` resolve-body docstrings, and both files are on the **do-not-revert** list as the maintainer's concurrent work. The sub-check's requirement is that the strings be right in the same pass as the prose; they are. Recorded plainly: this content did **not** arrive through Slice 5's own diff, and the tick is for the state, not for authorship. |
| `examples/fakeshop/test_query/README.md` | **landed** | `:5` states outright that `test_transport_api.py` "is made of nothing else" and enumerates the hostile-`Host` / `secure=` / `enforce_csrf_checks=` / `AsyncClient` rows, the in-process `ASGIHandler` driver, the real `multipart/form-data` control fields and the `Client(enforce_csrf_checks=True)` ordering row with its upload-handler sentinel — i.e. the file says it rather than leaving it to inference, which is the sub-check's own test. `:15` adds the file to the sibling enumeration; `:17` carries the S1 / S2 / S9 acceptance rows. |
| Slice-2 prose corrections | **landed** (two authored, two verify-only) | authored: `views.py::_RequestBodyBoundaryMixin`'s docstring now gives the precedence reason and says explicitly that mixin-first is *not* what satisfies `View.as_view`'s `hasattr` guard; `tests/test_views.py`'s mixin-privacy test carries three assertions, none about `__all__`. verify-only on the maintainer's dirty files: `conf.py #"EXCEPT for a multipart request"` plus `#"is REQUIRED ALONGSIDE this one"`; the `413`-is-inaccurate clause is gone from `test_transport_api.py`'s two-ceilings row. |
| Slice-3 prose correction | **satisfied, premise falsified** | `test_transport_api.py`'s first line reads `(spec-046 Slices 1-3)` on disk **and at `HEAD`** — I re-confirmed with `git show HEAD:… \| head -1`. The instruction is discharged; the sub-check's premise sentence was not, and I corrected the spec rather than carrying it to `bld-final.md` (see `### Spec changes made (Worker 1 only)`, edit 6). |
| card flip + `KANBAN` regeneration | **landed** | `KANBAN.md:98` (`## WIP / DONE spec map`) and `:1340` (`## Done`) both read `DONE-046-0.0.15`; `WIP-ALPHA-046` is absent from the file; `import_spec_terms --check` -> `OK: 46 done cards have glossary links.` DoD boxes 0-4 `- [x]`, box 5 `- [ ]` as Ruling 4 decided. |
| no version quintet, no `CHANGELOG.md` | **honoured** | `git status --short` names none of `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `CHANGELOG.md`; `pyproject.toml:4` is still `version = "0.0.14"`. |

**Builder's required-amendment list, discharged item by item.** Items 1, 4-8 were the plan's own
and were re-verified. Items 2 and 3 were discharged in the direction the plan chose. Item 9 is
**ruled** below (2d) and routed; item 10 is **done** (2a); item 11 is **done** (edit 5); item 12
needs no spec edit and I decline it with the reason recorded (a bold lead-in inside a paragraph
creates no anchor and the Doc-updates bullet enumerates *obligations*, not the guidance's
paragraph boundaries); item 13 asserts only that `M4` / `M5` were untouched, which I confirmed.
Nothing recorded-and-unimplemented remains, so no `revision-needed` on that axis.

**Declarations honoured, not merely agreed with.** `### Failability proofs` reads the required
literal and the diff introduces no guard, cap, rejection path or validation branch — I re-read
`git diff HEAD --` over both `.py` files and every hunk is docstring text. `### Hot-path budget`
and `### Floor verification` both read their `none` literals with reasons, and the two conditions
that would falsify them are absent: no executable line changed, and no Django / Strawberry /
channels seam is touched. No `uv pip install` ran in this pass and the shared `.venv` is
unmutated. The build-wide **M4** / **M5** escalations are untouched here.

**Fail-open sweep.** Read for the catalogued shapes rather than trusting the green suite: the
diff contains no clamp, `getattr` default, `or` fallback, bare `except`, or truthiness test on a
possibly-absent value, because it contains no executable change at all.

### The extra check: every spec claim about the shipped boundary, re-tested against the code

This is the check that found Decision 7 step 3's false multipart hand-off at the round-2 gate,
and its lesson was to scope the sweep to the whole shipped boundary rather than to the decisions
a round amended. Run again over `## Current state`, `## User-facing API`, Decisions 1-15,
`## Edge cases and constraints` and `## Definition of done` — the least-reviewed surface, since
rounds 1 and 2 amended Decisions 7 and 16-19.

**Two divergences found, both in Decision 8, both fixed this pass** (edits 3 and 4 below). Both
are the same class as the round-2 find: a decision stating the *looser half* of a rule the code
implements more strictly, propagated outward into the prose surfaces written from it.

1. **The multipart carve-out was stated unscoped** where `views.py::_is_multipart_form_post`
   returns `request.method == "POST" and request.content_type == _MULTIPART_CONTENT_TYPE`. This
   is Worker 3's **L3** and it is *the same sentence-shape* as the round-2 find, one decision
   away — Decision 7's own method-scoping paragraph (added at that gate) states the scope
   correctly, and Decision 8 was never brought into line with it. Direction: **understates**
   enforcement, so nothing is exposed; the sentence is still not true as written, and it is the
   source every other telling was copied from.
2. **Decision 8 named a header knob as a body cap.** `--limit-request-field-size` bounds a
   header field. `docs/README.md:358` — written *from* this decision and then corrected against
   the installed packages — says so explicitly and is **better than the spec**. That is the
   inversion worth naming: the doc out-ran the contract, so the contract moved.

Everything else in that surface held. Spot-checks I ran rather than assumed: the `413` / `400`
ceiling discrimination and its `"Request body exceeded the configured GraphQL request-body
limit."` reason; `4403` / `"Forbidden"` as a whole-connection close with the pending frame
suppressed and no preceding operation error (`consumers.py #"Revocation is connection-scoped"`);
`DisallowedHost` as the only normalized denial; the two revalidation checkpoints and the frame
set; `websocket_url_pattern=r"^graphql/?$"`; the required `django_application`; the
`1_048_576` default and the `None`-in-the-setting versus `None`-as-the-keyword split.

### Ruling — M1 (Worker 3, Medium): `routers.py`'s public constructor docstring

**Confirmed independently, not inherited.** Read-only verification, both sides:

```shell
grep -n "revalidates the session" django_strawberry_framework/routers.py     # -> 405:
git show HEAD:django_strawberry_framework/routers.py | grep -n "rejects the operation"  # -> 406:
git diff HEAD --stat -- django_strawberry_framework/routers.py               # -> empty
```

The false clause, at `django_strawberry_framework/routers.py:405-407`, inside
`DjangoGraphQLProtocolRouter.__init__`'s **public** docstring — the text a consumer reads while
choosing `websocket_revalidation_window=`:

> ``consumers.py::GraphQLWebSocketConsumer``, which revalidates the session actor **before every
> operation** and **rejects the operation - not the socket -** when the session is no longer
> valid.

**The true contract, with its source line.** `django_strawberry_framework/consumers.py:1` and
`:15-22`: revalidation happens at **two** checkpoints — operation admission (`handle_subscribe` /
`handle_start`, `:15`) and the outbound information-bearing frame (`next` / `data` /
operation-scoped `error`, through the `websocket_adapter_class` seam, `:18`). And
`consumers.py:52-58`, verbatim:

> **Revocation is connection-scoped.** The first failed validation - at either checkpoint -
> atomically marks the connection revoked, suppresses the pending frame, closes the whole socket
> with upstream's own ``4403`` / ``"Forbidden"``… the actor is connection-scoped so the close IS
> the rejection.

So **both halves** of the docstring sentence are false: "before every operation" understates the
checkpoint count, and "rejects the operation - not the socket" states the opposite of what
happens. `git diff HEAD` on `routers.py` is empty, so it is **pre-existing at `HEAD`** and not
Slice 5's regression.

**Ruling: the cross-slice integration pass owns it. Slice 5 is not held.** Reasons, in order:
the file is on Slice 5's must-not-touch list, so closing it here would be a worker writing
outside its declared ownership; nothing in Slice 5's diff caused it, and Slice 5 corrected the
other four tellings of the same contract; and the integration pass's remit is **exactly**
cross-slice inconsistency — a contract told in five places with one drifted telling is that
remit's definition, not an adjacent concern. Rejected alternatives: a one-paragraph Worker-2
re-loop scoped to the docstring (rejected — it spends a full plan/build/review/verify cycle on
one sentence the integration pass reads anyway, and the pass has to read the other four tellings
regardless to confirm consistency); routing it to the maintainer with the joint `0.0.15` cut
(rejected outright — it would ship a false security claim on a **public** constructor in a
released version, which is the one outcome none of the paths may produce).

**Routing record — the integration pass must close this. Do not close it by omission.**

- **File / line:** `django_strawberry_framework/routers.py:405-407`, in
  `DjangoGraphQLProtocolRouter.__init__`'s docstring (symbol-qualified:
  `routers.py::DjangoGraphQLProtocolRouter.__init__ #"revalidates the session"`).
- **False clause, quoted:** "revalidates the session actor before every operation and rejects
  the operation - not the socket - when the session is no longer valid."
- **True contract, with source:** two checkpoints (`consumers.py:12-22`), and revocation is
  connection-scoped — the socket is closed with `4403` / `"Forbidden"` and the close *is* the
  rejection, with no preceding operation error (`consumers.py:52-58`;
  `_REVOCATION_CLOSE_CODE = 4403` / `_REVOCATION_CLOSE_REASON = "Forbidden"` at
  `consumers.py:197-198`, applied at `:506`).
- **Severity and why it is not Low:** a false claim about security behavior on a public API
  surface. A consumer reading it would believe their socket survives revocation.
- **Constraint on the fix:** the two `websocket_revalidation_window` sentences that follow it are
  **true** and must survive; the correction is scoped to the two clauses quoted above. `0.0.14`'s
  released docstring is not a compatibility surface, so there is nothing to preserve.

### Ruling — L1 (Worker 3, Low): the stray comma in the rendered glossary

**Confirmed myself.** `grep -n "scope,\." docs/GLOSSARY.md` prints `327:`, inside
`## Channels request adapter`: "…to split a Channels HTTP scope from a WebSocket scope**,.**
Since spec-046 the package router serves no HTTP at all…". At `HEAD` the same sentence read
"…from a WebSocket scope**, and** `login` / `logout` now run over Channels HTTP consumers too",
so the rewrite replaced the tail and left the comma. **New this pass, in a rendered standing
doc.**

**Ruling: a routed follow-up, not my edit and not a Slice-5 re-loop.** `docs/GLOSSARY.md` is
rendered from `examples/fakeshop/db.sqlite3`; a hand-edit of the rendered file is silently
reverted by the next render, and the render is not on my writable list. It is one character in
one column, so a full slice re-loop is the wrong instrument; and it is cosmetic, in the one place
this build's own regenerate can fix it for free.

**Routing record.** Target: `GlossaryTerm` **id 529**, anchor `channels-request-adapter`, column
`body`; delete the comma in `"…from a WebSocket scope,. Since spec-046…"` so it reads
`"…from a WebSocket scope. Since spec-046…"`. Then `uv run python scripts/build_glossary_md.py`
and confirm `grep -c "scope,\." docs/GLOSSARY.md` is `0` and the regenerate is byte-stable
across two runs. Owner: whichever pass next legitimately writes the glossary DB — the
**cross-slice integration pass** if it opens one, otherwise the joint `0.0.15` cut, which is
already going to write this table for 2d below. `title` and `anchor` stay untouched.

### Rulings on 2b, 2c, 2d, 2e

**2b — L3, the five-surface multipart scoping.** My half is done: Decision 8 now states the
carve-out POST-scoped and makes stating the scope part of the Slice-5 prose contract (edit 4).
The other four surfaces are **not mine** and are recorded here so the item cannot close by
omission — each named individually, because a "five surfaces" summary is exactly how one gets
dropped:

1. `docs/README.md:360`, the `**Multipart is a carve-out, not a byte count.**` paragraph of
   `### Transport deployment guidance` — "For a `multipart/form-data` request the bound is the
   declared `Content-Length` plus Django's own `MultiPartParser`, and nothing else." Slice 5's,
   **closed**. Owner: the integration pass or the joint cut.
2. `docs/GLOSSARY.md` `## Request-body cap` (`:1476`), the sentence "**`multipart/form-data` is a
   carve-out**: its bound is the declared `Content-Length` plus Django's own `MultiPartParser`
   and nothing else". **DB-backed** — `GlossaryTerm.body`, anchor `request-body-cap`; fix in the
   DB and regenerate, never as text. Pairs naturally with L1 above and 2d below: one DB pass,
   one regenerate.
3. `django_strawberry_framework/conf.py #"EXCEPT for a multipart request"` — the
   `MAX_REQUEST_BODY_BYTES` key comment. **Source, and the maintainer's concurrent dirty work:
   never edit it, never revert it.** Maintainer-sequenced only.
4. `django_strawberry_framework/views.py #"**Multipart.** Bounded by the declared-size gate"` —
   the cap-contract docstring paragraph. Source; not a doc slice's to change.

Recommended one clause for all four, so the four tellings do not diverge again: *"on a multipart
**POST** — the carve-out is POST-scoped, and a multipart content type on any other method is
counted like any other body, which is the stricter direction."* That is `views.py`'s own
`_is_multipart_form_post` docstring wording, so it introduces no fifth phrasing.

**2c — the `--limit-request-field-size` knob. Worker 3 is right and the doc is right.** Fixed in
the spec (edit 3), and the rationale companion records *why the doc won*: the guidance was
written from the decision and then corrected against the installed packages, so the more accurate
text is downstream of the less accurate one. No follow-up: `docs/README.md:358` needs no change,
and the spec now matches it.

**2d — `status_text = "shipped"` on the seven new glossary entries. Ruling: the joint `0.0.15`
cut's, not this card's.** Three reasons, in decreasing order of force. (a) Decision 15 assigns
the `0.0.15` status flip to the cut and card `050` is still `todo` on that line, so this card
stamping `0.0.15` would be this card taking a step the cut owns. (b) The stamp would be
**false today**: the version quintet reads `0.0.14` on disk, so `shipped (0.0.15)` would name a
version that exists in no released artifact. (c) Bare `shipped` is not a defect: 16 entries in
the rendered file now use it, the status legend defines it as "implemented, tested, available in
the current package surface", and that is true of all seven. So the builder's `status_text`
choice is **upheld**, not merely tolerated.

Routed follow-up, with the exact string so the cut does not have to re-derive it: at the joint
`0.0.15` cut, set `GlossaryTerm.status_text` to ``shipped (`0.0.15`).`` on the seven anchors
`djangographqlview`, `request-body-cap`, `utf-8-wire-contract`,
`websocket-consumer-injection-seam`, `websocket-host-boundary`,
`websocket-revalidation-window`, `connection-scoped-revocation`, then regenerate. It travels with
the `README.md` / `TODAY.md` "Coming next" -> "Shipped today" move and the
`djangographqlprotocolrouter` entry's own ``shipped (`0.0.14`)`` -> `0.0.15` question, which have
the same owner. **Not my edit:** `docs/GLOSSARY.md` is rendered and a hand-edit is reverted by the
next render; a DB write is not on this pass's writable list.

**2e — builder notes 11-13 and L6.** Note 11 (the TREE bullet undercount) is **fixed in the
spec** (edit 5), and the bullet now says the render is source-driven so the list is what it
publishes rather than a ceiling on it — an enumeration of a generated artifact goes stale by
construction. Note 12 is **declined with the reason recorded** above (a bold lead-in creates no
anchor; the Doc-updates bullet enumerates obligations, not paragraph boundaries) — declined, not
`revision-needed`, because the target is the spec and `revision-needed` routes to a worker who
cannot edit it. Note 13 needed no action and was confirmed. L6 is artifact-side, so it is
**appended** below rather than edited into Worker 3's or my predecessor's text.

### Correction appended to Worker 3's L6

Worker 3 is right and I am recording the correction against my own predecessor's text without
touching it. `### Ruling 5`'s prose says "all **eleven** `0.262.0` mentions" and "**Six
corrections, five keeps**"; its own table carries **twelve** rows (6 CORRECT, 6 KEEP), and I
re-ran both counts myself: `git show HEAD:docs/SPECS/spec-041-channels_router-0_0_14.md | grep -c
"0\.262\.0"` prints **12**, and the working copy prints **8** (12 minus the four lines whose only
`0.262.0` was corrected, the other two corrections being in-place rewrites, plus the banner's two
own quotations). **The table is authoritative; the prose is what is wrong.** Worker 2 followed
the table and was right. The canonical count is therefore **twelve mentions, six corrections,
six keeps** — recorded here so it is not re-derived a fourth time.

### Spec changes made (Worker 1 only)

Seven edits, all quoted. Byte counts: `docs/spec-046-transport_security-0_0_15.md`
**226,343 -> 227,601** (+1,258); `docs/spec-046-transport_security-0_0_15-rationale.md`
**64,734 -> 69,226** (+4,492); `docs/SPECS/spec-041-channels_router-0_0_14.md` **150,070 ->
150,218** (+148, the Status line alone; `HEAD` was 147,420 and the rest is Slice 5's banner and
corrections).

1. **`docs/SPECS/spec-041-channels_router-0_0_14.md:90`, the `Status:` line only** (job 2a).
   Was: `Status: **PLANNED — no slice built yet.**` — factually wrong: the card is
   `DONE-041-0.0.14` (`KANBAN.md:103`, `:1777`) and both its slices shipped, and the amendment
   banner Slice 5 added two dozen lines above it says "the Status line remains the source of
   truth", which made the contradiction self-referential. Now:
   `Status: **COMPLETE** (card \`DONE-041-0.0.14\`) — both slices built and the card wrap landed;`
   `the \`0.0.14\` release rode the joint cut. Amended by [\`spec-046\`][spec-046]; see the banner`
   `above.` The `**COMPLETE** (card \`DONE-NNN-X.X.X\`)` shape is this repo's existing convention
   for a shipped spec (`spec-035:5`, `spec-042:55`), and `[spec-046]` reuses the link definition
   Slice 5 already added at `:2167`. **No checkbox anywhere in that file was touched** and the
   opening `Planned for 0.0.14` paragraph is untouched, per the shipped-card closeout convention.
2. **Spec `:3`, the opener's card id.** `WIP-ALPHA-046-0.0.15` -> `DONE-046-0.0.15`, falsified by
   this slice's own card flip. `Planned for \`0.0.15\`` stays: the target release is still a
   target.
3. **Spec `:37-42`, the `Status:` line** (mandatory per `worker-1.md`
   `## Spec status-line re-verification`). Was `**IN BUILD — Slices 1-4 (S1, S2, S9, S11) are
   built … Slice 5 remains.**` — falsified the moment Slice 5 landed. Now `**BUILT — all five
   slices (S1, S2, S9, S11, and the S12 transport slice) are built, with [Decisions 16-19]'s
   contracts landing inside them. The \`0.0.15\` release itself is the joint cut's ([Decision
   15]), so the version quintet still reads \`0.0.14\` on disk.**` The second sentence is added
   because "BUILT" alone invites the wrong inference about the release.
4. **Decision 8, the "concrete directions" list** (job 2c). Was `(\`client_max_body_size\` on
   nginx, \`--limit-request-field-size\` / equivalents on the ASGI server, and the note that
   Daphne's request-buffer size controls fragment delivery rather than total accepted body)`.
   Now names `LimitRequestBody` on Apache as the second real directive and states that **no
   mainstream ASGI server bounds the total body at all** — Uvicorn, Hypercorn and Daphne ship no
   total-request-body limit and the knobs they expose bound the request line and headers — plus
   one sentence saying why that matters: *"Naming a header-shaped knob as if it capped the body
   would hand the reader exactly the false comfort this decision exists to remove: the proxy line
   is load-bearing **because** the layer below the application supplies nothing."*
5. **Decision 8's Slice-5 bullet, the multipart carve-out** (job 2b, L3). Was `(for a multipart
   request the bound is the declaration plus Django's \`MultiPartParser\`, not a byte count)`.
   Now `(on a multipart **POST** — the one request shape \`views.py::_is_multipart_form_post\`
   admits — the bound is the declaration plus Django's \`MultiPartParser\`, not a byte count; a
   multipart content type on any other method takes the counted path like any other body, per
   [Decision 7]'s method scoping, and the carve-out must be stated with that scope so a reader
   cannot read the looser half as the whole rule)`. The trailing clause is deliberate: it makes
   stating the scope part of the **prose obligation**, so the next writer of that paragraph
   cannot reproduce the unscoped form from the decision again.
6. **`## Doc updates`, the `docs/TREE.md` bullet** (builder note 11). The tail `; plus
   \`tests/test_views.py\` in the test trees.` becomes `; plus \`tests/test_views.py\`,
   \`examples/fakeshop/test_query/test_transport_api.py\` and \`tests/test_prove_failability.py\`
   in the test trees, and corrected \`routers.py\` / \`tests/test_routers.py\` rows.` plus one
   sentence stating the render is source-driven so the list is not a ceiling. I verified each
   named row exists: `docs/TREE.md:628`, `:449`/`:661`, `:454`/`:666`.
7. **`## Slice checklist`, Slice 5's `test_transport_api.py` sub-bullet.** The premise `the module
   docstring's **first line** still scopes the file to \`(spec-046 Slices 1-2)\` although it now
   also carries … — correct it to the file's actual slice scope` becomes `the module docstring's
   **first line** must name the file's actual slice scope, which now also covers … — confirm it
   does and correct it if it does not`. The premise was true when written and was falsified by
   Slice 3's own docstring edit, so the closing slice was reading a contract describing a state
   two slices earlier. **Deliberate consequence, recorded rather than hidden:** this artifact's
   `### Spec slice checklist (verbatim)` still carries the pre-correction wording, because it is
   the record of what was dispatched and rewriting it would desync the evidence. The precedent
   this follows is the build plan's own ruling on Slice 3's `:203-208` sub-bullet, which turned on
   that sentence being *incomplete* rather than *false*; this one was false.

**Rationale companion (append-only, same pass).** Two change records under `### Decision 8` — the
header-knob correction and the POST-scoping correction, each with its rejected alternative and the
direction of the drift — plus a new `### Change record for the spec's non-decision sections` under
`## Program provenance`, covering edits 2, 3, 6 and 7, which have no decision entry to belong to.

### Mechanical verification of the spec edits — four ways, none by eye

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md`
  -> `OK: 37 terms - all have glossary entries and at least one spec link.` (exit 0).
- **Every in-page anchor resolves.** Slugified every heading in both edited specs (fence-aware,
  keeping `_`, stripping backticks) and matched all `](#…)` uses: `spec-046` **23 anchors, 0
  missing**; `spec-041` **23 anchors, 0 missing**. Also re-checked `docs/README.md` (3 anchors, 0
  missing), so edit 1's new `[spec-046]` use and the banner's copied anchors all land.
- **Every reference-style definition is used and every use is defined**, in all three files:
  `used-not-defined: []`, `defined-not-used: []`. No cross-reference points into moved text
  without naming the rationale file — the two new Decision-8 change records are cited from the
  decision's own `*Rejected alternatives and change record*` pointer, which already existed.
- **Zero self-narration.** `grep -i "review round\|worker \|pass [0-9]"` over the spec returns
  exactly one line, `:2625`, and it is a pytest-xdist worker inside a test-plan row, not a build
  worker. No "review round", no "pass N".

### Gates run in this pass

| gate | result |
|---|---|
| `uv run pytest --no-cov` | **5202 passed, 40 skipped** in 55.75s — exactly the declared baseline |
| `uv run pytest tests/test_views.py tests/test_routers.py --no-cov` | **266 passed** (144 + 122, both declared counts) |
| `uv run python scripts/check_spec_glossary.py --spec …spec-046…md` | `OK: 37 terms`, exit 0 |
| `uv run python examples/fakeshop/manage.py check` | `System check identified no issues (0 silenced).` |
| `uv run python scripts/build_tree_md.py --check` | `docs/TREE.md is up to date.` exit 0 |
| `uv run python examples/fakeshop/manage.py import_spec_terms --check` | `OK: 46 done cards have glossary links.` exit 0 |
| `uv run ruff format --check .` / `uv run ruff check .` | `405 files already formatted` / `All checks passed!` — **read-only**, no write-mode `ruff` ran, so the open `AGENTS.md:15` conflict was never touched |
| `uv run python scripts/check_trailing_commas.py --check <3 explicit paths>` | exit 0, no output. Explicit paths on the only invocation, so `drys.md` / `vulns.md` were unreachable |
| `git diff --check` | exit 0 |
| `git status --short` | **19 `M` + 4 `??`, byte-for-byte the list I found.** My four writable paths are among them; nothing else moved, so there was nothing to stop-and-report and nothing was reverted |

No `--cov*` flag was used anywhere in this pass. No `git` write command ran: no commit, branch,
stash, `git add`, `git checkout` or `git restore`. The `git show HEAD:` reads in the M1 and L1
verifications are read-only by construction.

### What the cross-slice integration pass must own

Consolidated so Worker 0 can build the next dispatch's scope from one list. The first two are
**binding** from prior passes; items 3-5 are this pass's rulings.

1. **BINDING** — `examples/fakeshop/test_query/test_transport_api.py`: extract a shared
   `_user_who_can_add_categories()` helper across its **2** sites.
2. **BINDING** — the same file: rewire the **six** inline `await ….post(...)` blocks onto the
   existing `_post_bytes`.
3. **M1** — `routers.py:405-407`'s public constructor docstring, with the full routing record
   above. This is the pass's own remit (one contract, five tellings, one drifted) and it must not
   close by omission.
4. **L3's remaining surfaces**, individually named in 2b above. `docs/README.md:360` and the
   `Request-body cap` glossary body (DB) are actionable by this pass; `conf.py` and `views.py`
   are source and maintainer-sequenced, so the pass records them rather than editing them.
5. **L1** — the one-character `GlossaryTerm` id 529 fix plus a regenerate, if this pass opens the
   glossary DB at all; otherwise it travels to the joint cut with 2d.
6. **Cross-file repeated literals** across the six doc surfaces are already grep-verified clean
   by Worker 3 (`client_max_body_size` at exactly one site, `README.md` / `TODAY.md` prose-only),
   so the pass can cite that rather than re-deriving it.

### For `bld-final.md`'s `### Deferred work catalog`

- **2d** — the seven glossary `status_text` stamps at the joint `0.0.15` cut (exact string and
  seven anchors above), beside the `README.md` / `TODAY.md` "Coming next" -> "Shipped today" move
  and the `djangographqlprotocolrouter` entry's `0.0.14` -> `0.0.15` question.
- **The terms CSV stays at 37 rows.** Ruling 3's reasoning is sound and Worker 3 endorsed it; if
  the maintainer wants card 046's link set to include the seven terms it authored, that is one
  Worker-1 pass editing the CSV **and** the spec's `## Key glossary references` + link-def block
  together, then re-running `import_spec_terms` and `build_glossary_md.py`.
- **`definition_of_done` order 5 stays unticked** — coverage is the maintainer's gate and the
  full-suite / lint / `manage.py check` sweep runs after this slice. Owner: the maintainer, after
  the final gate. This is the one-line deferral Ruling 4 said I would record.
- **L4** — the one clause `docs/README.md:360` could gain about body-reading project middleware.
  Ruling: **path (c) plus a nudge.** Decision 8 does not require it,
  `views.py::_run_after_csrf_check` already carries it in bold for a code reader, and the counted
  half of the same section already states its own honest boundary — so the code docstring is the
  authoritative statement. Recorded rather than closed, because the party who owns the caveat is
  exactly this section's reader; the maintainer may prefer path (a).
- **L2** — `README.md:62`'s `0.0.14` paragraph describes `main`'s router shape inside the released
  version's sentence. The framing choice is mine and I take Worker 3's first option: lead with the
  marker, the shape `docs/README.md:128` and `TODAY.md:384` already use. `README.md` is Slice 5's
  and closed, so this is a catalog entry for the joint cut, which is rewriting that paragraph
  anyway for the "Shipped today" move.
- **L5** — `BACKLOG.md:1616` / `:1661` describe the router as serving HTTP + WebSocket in the
  present tense. Deliberately outside the spec's `## Doc updates` set.
- **Do not act** — closed `docs/review/`, `docs/dry/` and `docs/bug_hunt/` scratchpads still
  assert the old "UTF-16 succeeds" contract. They are closed per-cycle records; leave them.
- **Still open maintainer items, untouched here:** `M4` (the literal weakly-pinned rule), `M5`
  (the build-wide hot-path declaration), and the `AGENTS.md:15`-vs-scoped-`ruff` conflict.

### One stale line left deliberately

This artifact's own `Spec reference:` header says `## Doc updates` sits at spec lines 2700-2768;
my seven edits shifted it to `:2721`. Left as written: it is a pin-at-write-time navigational hint
in a per-cycle scratchpad (`AGENTS.md` permits raw `path:NN` only here, and only because it closes
when the cycle does), and rewriting the plan's header is rewriting the plan. Every line number in
**this** section was re-read against the current files.

### Verdict

`final-accepted`. Every sub-check landed or was legitimately verify-only; every builder
amendment is discharged, done, or declined with a recorded reason; the three `none`
declarations were honoured rather than merely asserted; the two spec-vs-code divergences this
pass found are fixed in the spec, and the two findings that belong to files this slice could not
touch are ruled and routed with enough precision that neither can close by omission.
