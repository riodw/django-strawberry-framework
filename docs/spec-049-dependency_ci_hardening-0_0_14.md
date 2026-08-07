# Spec: Dependency and CI hardening — refresh the locks, audit the resolution on a clock, run CI at least privilege

> **AMENDED 2026-08-05 by maintainer decision — the declared Django floor moves to
> `Django>=5.2.16`.** This card argued against exactly that move and was overruled after the
> argument was heard. The reversal is recorded here rather than edited into the prose below,
> because a decision that was made and then reversed is two facts, not one.
>
> What the amendment changes:
>
> 1. **[Decision 1](#decision-1--the-lock-moves-the-declared-floors-do-not) — the
>    floor-raise refusal is superseded.** `pyproject.toml` now declares `Django>=5.2.16`
>    (`5.2.16` being the July 2026 security release that fixed CVE-2026-48588; `5.2.15` /
>    `6.0.6` fixed five more). Django `5.2.0`–`5.2.15` are **no longer supported at all** —
>    not merely not-recommended for deployment. Decision 1's *distinction* survives intact
>    and is still the right frame: a declared floor answers an API question and a lock entry
>    answers a today question, and the two must not be conflated. The maintainer simply
>    chose to move the compatibility line as well, accepting the cost Decision 1 names
>    (consumers pinned to an older supported patch must move) in exchange for refusing to
>    advertise API compatibility with a range nobody should install. What remains a category
>    error is the *reasoning* Decision 1 rejects — deriving a floor from a security
>    preference alone; the floor here is a support statement whose boundary happens to
>    coincide with a patched release.
> 2. **[Decision 2](#decision-2--the-5-2-0-cell-is-a-compatibility-contract-not-a-deployment-target)
>    — the cell's contract stands; only its installed version moves.** The exact-floor CI
>    cell now installs `Django==5.2.16` and **keeps** its `compatibility_only` key, its
>    `[compatibility floor]` job-name suffix, and its contract comment. Decision 2's
>    rejected alternative "moving the floor to `5.2.16` so the cell tests a patched
>    version … destroys the cell's purpose" was reasoning about a cell that tracked an
>    *unmoved* floor; with the floor itself at `5.2.16` the cell still tests the floor, which
>    is its whole purpose. The label is not decoration and does not retire: the floor is a
>    point-in-time API statement, so the first `5.2.17` security release makes the floor
>    older than the newest patch again. The "install the newest patch in your series" rule
>    therefore survives the raise unchanged, and so does the cell's prohibition on being
>    cited as a deployment target.
> 3. **[Goals](#goals), [Non-goals](#non-goals),
>    [Implementation plan](#implementation-plan) row 2, and the
>    [Definition of done](#definition-of-done) floor row** are annotated in place. Their
>    original text records what this card built and is left standing; each carries an
>    **Amendment (2026-08-05)** note stating the post-amendment truth.
>
> What the amendment does **not** change: every other decision, the lock refresh, the CI
> least-privilege posture, the audit and Dependabot automation, the governance test, and the
> secure-version statement — which is *more* necessary after the raise, not less, since a
> raised floor is still a floor. Checkbox state throughout this spec is untouched; the
> `Status:` line remains the completion source of truth per this repo's shipped-card closeout
> convention.

Targeted at `0.0.14` (card [`WIP-ALPHA-049-0.0.14`][kanban]). This is **card 4 of 4**,
the last card of the four-card security-remediation program derived from the hardening
audit in [`docs/feedback2.md`][feedback2]; it closes that audit's **S6** (the locked Django
resolution predates published security releases, and no audit / update automation exists)
and **S7** (the CI workflows over-grant, persist credentials, pin mutably, and never time
out). It follows [`spec-046`][spec-046] (transport security), [`spec-047`][spec-047] (the
execution resource policy), and [`spec-048`][spec-048] (secure output and error defaults),
and completes the program.

**`docs/feedback2.md` is review evidence this spec references, not a substitute for it.**
The audit established the facts; every decision, tool choice, pin, and test row below is
this spec's own.

**This card changes no package source.** Nothing under `django_strawberry_framework/`
moves, the generated SDL is byte-identical, and no settings key is added. The deliverables
are the dependency lock, four workflow files, one Dependabot configuration, and one
governance test. That boundary is the point: the three preceding cards changed what the
package *does*, and this one changes what the project *ships and proves* — a distinction
worth keeping visible, because a governance card that quietly grows a source diff is a
governance card nobody can review.

Status: **SHIPPED — all five slices are built and released.** The `Status:` line is the
completion source of truth (the shipped-spec convention); the Slice checklist boxes below
stay unticked. Card [`DONE-049-0.0.14`][kanban] closes the four-card security-remediation
program. `CHANGELOG.md` carries no `0.0.14` entry — [`AGENTS.md`][agents] reserves that
entry for the maintainer.

**Version boundary** (see
[Decision 10](#decision-10--the-version-bump-belongs-to-the-0014-joint-cut)):
this card targets `0.0.14`, which the version quintet already reads, so its Slice 5 owns
the documentation fold-in and no part of the quintet. As the last card of the four-card
program to land, it is the natural owner of the
[Joint version cut][glossary-joint-version-cut]'s release wording whenever that cut is
taken.

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits without explicit
permission. This card's Slice 5 does **not** claim that permission — the release entry is
the maintainer's.

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [Hard dependency][glossary-hard-dependency] — Django and `strawberry-graphql`, the
  unconditionally-installed packages whose resolved versions this card refreshes and whose
  declared floors it deliberately leaves alone.
- [Soft dependency][glossary-soft-dependency] — the optional-extra architecture. It matters
  twice here: `cryptography` is a soft dependency whose locked version the audit flagged,
  and the "dependency gate adds the dev-group row and regenerates `uv.lock` in the same
  commit" discipline is the precedent this card's own dev-group addition follows.
- [`require_optional_module`][glossary-require_optional_module] — the single optional-import
  owner; named to make explicit that this card adds no new optional-import surface.
- [Per-operation extension isolation][glossary-per-operation-extension-isolation] — the
  advertised `strawberry-graphql==0.316.0` floor that the compatibility matrix cell exists
  to exercise, and therefore part of why that cell must survive this card.
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the test-placement
  rule that puts the governance test in root `tests/`: a workflow YAML file is not
  reachable from a fakeshop `/graphql/` request by any route.
- [Joint version cut][glossary-joint-version-cut] — the release rule this card is
  explicitly NOT subject to, and whose "`uv.lock` **dependency** entries are not version
  state" clause authorizes the lock refresh to land with this card.

This spec adds no glossary term. It ships no consumer-visible symbol, so there is nothing
for the capability catalogue to describe; Slice 5's glossary work is the package-version
line and the security-posture note described in [Doc updates](#doc-updates).

## Slice checklist

Each top-level item maps to one commit / PR.

- [ ] **Slice 1 — the lock refresh**
      `uv.lock` moves Django to `5.2.16` (`python_full_version < '3.12'`) and `6.0.7`
      (`>= '3.12'`), and moves `cryptography` and `pillow` off the versions the audit
      flags. `pyproject.toml` dependency floors are untouched
      ([Decision 1](#decision-1--the-lock-moves-the-declared-floors-do-not)).
      **Amendment (2026-08-06):** the lock tracks the top of the AUDITED range, not a
      version frozen at authoring time, because an unpinned CI node resolves from the lock
      and a stale one turns every such node into a second floor run — leaving the
      top-of-range tripwires silent on a green board. Django 6.1 was audited and supported
      the same day it broke the unbounded range, so the lock now reads `5.2.17` / `6.1`.
      The declared floors still do not move.
- [ ] **Slice 2 — least-privilege CI**
      `.github/workflows/django.yml`, `postgres.yml`, `kanban-pages.yml`: top-level
      `permissions: contents: read`, the test job's `contents: write` deleted,
      `persist-credentials: false` on every checkout, every `uses:` pinned to a full commit
      SHA with a readable version comment, the Postgres image pinned by digest, and
      `timeout-minutes` on every job. The Django 5.2.0 cell is relabelled
      compatibility-only, not removed
      ([Decision 2](#decision-2--the-5-2-0-cell-is-a-compatibility-contract-not-a-deployment-target)).
      **Amendment (2026-08-05):** that cell now installs `Django==5.2.16` — the raised
      floor — and keeps the compatibility-only labelling verbatim.
- [ ] **Slice 3 — audit and update automation**
      `.github/workflows/dependency-audit.yml` (new): `osv-scanner` against `uv.lock` on
      pull requests, on a daily schedule, and on dispatch. `.github/dependabot.yml` (new):
      the `uv` and `github-actions` ecosystems.
- [ ] **Slice 4 — the governance test**
      `tests/test_ci_governance.py` (new) asserts the Slice 2 and Slice 3 posture
      structurally; `pyproject.toml` gains the `pyyaml` dev-group row it needs.
- [ ] **Slice 5 — docs fold-in and the version cut**
      `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`,
      and `KANBAN.md`. The version quintet is the joint cut's, not this slice's.

## Problem statement

Two independent gaps, both in the project's supply chain rather than its code.

**The resolved dependency graph is stale, and nothing would have told us.** `uv.lock`
resolves Django `5.2.14` under `python_full_version < '3.12'` and `6.0.5` under
`>= '3.12'`. The Django project has since shipped `5.2.15` / `6.0.6` (five fixes) and
`5.2.16` / `6.0.7`, the latter carrying CVE-2026-48588, a shared-cache private-data
exposure. Neither release reached this repository, because the repository has no mechanism
by which it could: there is no audit command, no scheduled security workflow, and no update
configuration. The staleness is not the interesting part — a lock file is stale the moment
it is written. The interesting part is that the project had **no way to learn** it, and a
hand-refresh now would restore exactly the same condition tomorrow.

That this is not hypothetical is worth stating precisely, because the audit tooling this
card adds was run against the tree before the tree was fixed: scanning the pre-refresh
`uv.lock` reported **14 known vulnerabilities across two packages** — `cryptography`
`49.0.0` (one high-severity advisory, fixed in `50.0.0`) and `pillow` `12.2.0` (thirteen
advisories, fixed in `12.3.0`) — neither of which is Django, and neither of which anyone
had noticed. `cryptography` is a [soft dependency][glossary-soft-dependency] real consumers
install, which makes it consumer-facing surface, not merely test scaffolding.

**CI runs with more authority than it uses, and less determinism than it needs.** Four
distinct problems, none of which has bitten yet:

- The `test` job in `django.yml` grants `permissions: contents: write`. The only consumer
  of a token in that job is the Coveralls upload, which authenticates a coverage report and
  has no reason to write to the repository. The grant is unused authority extended to every
  step in the job, including every third-party action and the entire installed dependency
  tree.
- Every `actions/checkout` invocation persists its credential into `.git/config` by
  default, leaving a usable token in the workspace for all subsequent steps. No job in this
  repository pushes anything, so the credential has no consumer at all.
- First-party actions are referenced by mutable major tags (`actions/checkout@v6`,
  `actions/configure-pages@v6`, `actions/upload-pages-artifact@v5`,
  `actions/deploy-pages@v5`), and the Postgres tier starts `postgres:16`. In every case the
  code or image executing in CI is whatever the reference points at on the day of the run,
  which is not a thing anyone reviewed.
- No job in `django.yml` or `postgres.yml` sets `timeout-minutes`. Every one of them
  installs from the network or runs the suite, so a hung download or a deadlocked test
  holds a runner until GitHub's six-hour default.

## Current state

- `uv.lock` resolves Django `5.2.14` / `6.0.5`, `cryptography` `49.0.0`, `pillow` `12.2.0`.
  `pyproject.toml` declares `django>=5.2`, `django-filter>=25.2`,
  `strawberry-graphql>=0.316.0`, `wrapt>=2.0.1`.
- `.github/workflows/` holds exactly three files: `django.yml` (lint + the
  Python/Django/database matrix, owner of the `fail_under = 100` gate and the Coveralls
  upload), `postgres.yml` (the manual five-shard Postgres tier), and `kanban-pages.yml`
  (the Pages export). `kanban-pages.yml` is already the best-behaved of the three: it
  alone declares a top-level `permissions: contents: read`, scopes its `deploy` job's extra
  `id-token: write` / `pages: write` to that job, and sets `timeout-minutes` on both jobs.
  It is the local precedent the other two are brought up to, not a new invention.
- `astral-sh/setup-uv` is already SHA-pinned with a trailing `# v8.1.0` comment, in all
  three workflows. That is the pin *style* this card generalizes to every other `uses:`.
- There is no `.github/dependabot.yml`, no audit workflow, and no test anywhere that reads
  a workflow file.

## Goals

- The locked Django resolution is at or above `5.2.16` and `6.0.7` on their respective
  Python markers, and no locked package carries a known advisory at authoring time.
- A vulnerability published against an already-locked dependency surfaces without anyone
  touching the repository.
- An update path exists that keeps immutable pins current instead of merely immutable.
- Every CI job holds the narrowest token scope that lets it do its work, executes only
  reviewed action code and container images, and bounds its own wall-clock time.
- The distinction between *compatibility support* and *secure-deployment support* is stated
  where it can be acted on, and the `django>=5.2` floor stops reading as a security
  recommendation. **Amendment (2026-08-05):** the floor is now `django>=5.2.16` and the goal
  is unchanged in substance — a floor at a patched release still is not a secure-version
  recommendation, because the next Django security release moves past it.
- The posture is asserted by a test, so it degrades loudly rather than silently.

## Non-goals

- No change to any package source file, the generated SDL, or any settings key.
- No change to the declared dependency floors in `pyproject.toml`
  ([Decision 1](#decision-1--the-lock-moves-the-declared-floors-do-not)).
  **Amendment (2026-08-05): superseded for Django.** The declared Django floor is now
  `Django>=5.2.16`; the other three floors are still untouched.
- No removal or weakening of the exact-Django-5.2.0 compatibility matrix cell
  ([Decision 2](#decision-2--the-5-2-0-cell-is-a-compatibility-contract-not-a-deployment-target)).
  **Amendment (2026-08-05):** the cell is neither removed nor weakened — it moves with the
  floor to exact `Django==5.2.16` and keeps its compatibility-only contract.
- No new coverage surface: `fail_under = 100` measures `django_strawberry_framework` only,
  and the governance test reads YAML.
- No SARIF upload to the code-scanning API, and therefore no `security-events: write`
  anywhere ([Decision 5](#decision-5--osv-scanner-against-uv-lock-on-a-clock-and-on-every-resolution-diff)).
- No self-hosted mirror, private registry, or artifact-signing posture. Out of scope and
  uncarded.

## Borrowing posture

There is no upstream primitive to borrow here, and it would be dishonest to invent one:
`graphene-django` and `strawberry-graphql-django` publish packages, not a CI governance
contract, and neither ships a surface this card could adapt. The DRF-shape argument that
governs the rest of the package does not reach a workflow file.

The reference points are therefore external and general rather than upstream and specific:
GitHub's own documented hardening guidance for Actions (least-privilege `permissions`,
third-party actions pinned to a full commit SHA, `persist-credentials: false` on checkouts
that do not push) and the OpenSSF Scorecard checks that mechanize it (`Token-Permissions`,
`Pinned-Dependencies`). Every posture item in Slice 2 maps to one of those, which is the
reason to prefer them over a locally-invented standard: they are the checks a downstream
consumer auditing this project will actually run.

The one genuinely local precedent is `kanban-pages.yml`, described in
[Current state](#current-state) — this card generalizes what that file already does rather
than importing a new convention.

## User-facing API

None. This card adds no importable symbol, no `Meta` key, no settings key, and no schema
change; the entire delivery is governance configuration plus one test.

The consumer-facing output is documentation, and it is a **security statement** rather than
an API: `django>=5.2` in `pyproject.toml` is the floor at which this package's API is
compatible, and it is **not** a statement that `5.2` is safe to deploy. Production
consumers must install the newest patch release in their supported Django series. Slice 5
places that sentence in `README.md` and `docs/README.md`, next to the supported-versions
table where a reader forms the belief the sentence has to correct. See
[Decision 2](#decision-2--the-5-2-0-cell-is-a-compatibility-contract-not-a-deployment-target).

**Amendment (2026-08-05):** substitute `django>=5.2.16` for `django>=5.2` throughout the
paragraph above and every word of it still holds. A floor sitting on a patched release is
still a compatibility statement frozen at release time, and a `5.2.17` will move the newest
patch past it. The statement lands in the user guide's
[Production security profile][docs-readme-production-profile] and, condensed, in
[`SECURITY.md`][security]'s deployment-hardening section.

## Architectural decisions

### Decision 1 — The lock moves; the declared floors do not

> **Amendment (2026-08-05) — the Django half of this decision is superseded by maintainer
> decision.** `pyproject.toml` declares `Django>=5.2.16`; Django `5.2.0`–`5.2.15` are
> unsupported, not merely undeployable. The distinction this decision draws between a
> compatibility floor and a lock entry remains correct and remains the reason the two files
> are edited for different reasons — the maintainer moved the compatibility line too, on the
> ground that advertising API compatibility with a range the project will not support is its
> own kind of false statement. The paragraphs below are the argument as it stood at build
> time and are left standing so the reversal is legible. The `cryptography` / `pillow` and
> lock-refresh halves of this decision are unaffected, as are the `django-filter`,
> `strawberry-graphql`, and `wrapt` floors.

`uv.lock` is refreshed to Django `5.2.16` / `6.0.7`, `cryptography` `50.0.0`, and `pillow`
`12.3.0`. `pyproject.toml`'s `[project].dependencies` are left exactly as they are.

The two express different things, and conflating them is the actual error available here.
A declared floor answers "below which version does this package's API stop working?" — for
Django that is genuinely `5.2`, and the exact-`5.2.0` matrix cell is the evidence. A lock
entry answers "which version does this project build, test, and install today?" — and that
must be the newest patch, always. Raising `django>=5.2` to `django>=5.2.16` to express a
security preference would be a category error with a real cost: it would break every
consumer pinned to a supported-but-older patch for reasons of their own, while doing
nothing for the consumer who resolves Django independently of this lock file — which is
every consumer, because a library's lock file is not installed.

The [Joint version cut][glossary-joint-version-cut] entry already draws this line from the
release side: "`uv.lock` **dependency** entries are not version state — a card's own
dependency-gate lock regeneration lands with that card." This card is that card.

The upgrade is scoped per package (`uv lock --upgrade-package django`,
`--upgrade-package cryptography --upgrade-package pillow`) rather than run as a bare
`uv lock --upgrade`, so the diff is reviewable and no unrelated transitive pin moves in the
same change. `uv lock --check` passing afterwards is what proves the refreshed lock is
still a valid resolution of the unchanged floors.

**`cryptography` and `pillow` are refreshed here, not deferred.** The card names Django;
these two were found by running this card's own audit tooling against the pre-refresh tree.
Landing an audit gate that is red on its first run is not a shippable outcome, and the two
available alternatives are both worse than fixing them: an ignore-list entry suppresses a
real advisory to make a dashboard green, and a follow-up card leaves the gate red in the
interim, which trains everyone to ignore it. `cryptography` in particular is a
[soft dependency][glossary-soft-dependency] consumers install for `Meta.cursor_field`
keyset cursors, so its advisory is consumer-facing.

**Alternatives rejected.** Raising the declared floors to the patched versions — a category
error, above. Pinning exact versions in `[project].dependencies` — makes the package
un-co-installable, the standard library anti-pattern. Adding an audit ignore-list for the
two non-Django findings — suppression, not remediation.

### Decision 2 — The 5.2.0 cell is a compatibility contract, not a deployment target

> **Amendment (2026-08-05) — the cell's contract survives; its version does not.** With the
> floor raised to `5.2.16` the exact-floor cell installs `Django==5.2.16` and keeps every
> label this decision gave it: the `compatibility_only` matrix key, the
> `[compatibility floor]` job-name suffix, the contract comment, and its exclusion from the
> audit's input. It still tests *the floor* — which is what this decision protects — because
> the floor is what moved. The labelling is not a leftover: a floor is a point-in-time API
> statement, so the next `5.2.x` security release again makes the floor older than the newest
> patch, and the "run the newest patch in your series" rule this decision establishes holds
> unchanged. Only the third rejected alternative below ("moving the floor to `5.2.16` so the
> cell tests a patched version") is superseded, and only as reasoning about a *stationary*
> floor. Read `5.2.0` below as "the exact floor at build time".

The exact-`Django 5.2.0` matrix cell stays, unchanged in what it installs. It gains a
`compatibility_only: "1"` matrix key, which renders a `[compatibility floor]` suffix into
the job name, and a comment block stating what the cell does and does not assert.

The cell earns its place: `django>=5.2` is an advertised floor, and an advertised floor with
no test is a guess. It is also the only node that force-installs
`strawberry-graphql==0.316.0`, so it is simultaneously the evidence for the
[Per-operation extension isolation][glossary-per-operation-extension-isolation] floor. Its
Its predecessors on this patch line did not remove it and neither does this card.

But `5.2.0` predates `5.2.15` and `5.2.16`, so a green tick on that cell is now adjacent to
a version carrying published advisories — and an adjacent green tick is exactly how a
reader concludes a version is endorsed. **Compatibility support and secure-deployment
support are different contracts**, and the mitigation is to make the cell say which one it
is at the three places a reader meets it: the rendered job name, the matrix comment, and
the supported-versions prose in `README.md`. The comment states the prohibitions
positively — this cell must never be cited as a supported deployment target, copied into a
deployment example, or used to argue that `django>=5.2` is a safe pin.

The cell is also, deliberately, **not audited**. The audit's scan target is `uv.lock`
([Decision 5](#decision-5--osv-scanner-against-uv-lock-on-a-clock-and-on-every-resolution-diff)),
and the `5.2.0` environment is constructed by a `uv pip install` override inside a job step
— it is not part of any resolution the audit reads. This is the card's "handle the
intentional 5.2.0 compatibility environment separately" requirement, and the separation is
structural rather than a suppression rule: there is no ignore-list entry to forget to
remove, because the compatibility environment was never in the audit's input.

**Alternatives rejected.** Dropping the cell — abandons the floor test and the Strawberry
floor test with it, to fix a labelling problem. Moving the floor to `5.2.16` so the cell
tests a patched version — destroys the cell's purpose, which is to test the *floor*, and
re-introduces Decision 1's category error. Adding the `5.2.0` environment to the audit with
an ignore-list — creates a permanent suppression that would mask a genuinely new advisory
against that environment.

### Decision 3 — Least privilege is a default plus a visible exception, not a per-job audit

Every workflow declares `permissions: contents: read` at the top level. The `test` job's
`permissions: contents: write` block is deleted outright rather than narrowed.

A job-level `permissions` block **replaces** the workflow default rather than merging with
it, which is the property that makes this shape work: the top-level block sets the floor
for every job, and any job needing more must restate its entire scope in one place, next to
the step that consumes it. The result is that a reader looking for elevated authority
greps for `permissions:` at job level and finds a complete list — in this repository,
exactly one entry, `kanban-pages.yml`'s `deploy` job with `id-token: write` / `pages:
write`, which is a genuine requirement of OIDC-authenticated Pages deployment.

Deleting the `test` job's grant rather than narrowing it is the correct move because the
correct scope is the inherited default. The only token consumer in that job is the
Coveralls upload; it authenticates a coverage report against Coveralls' API and never
writes to the repository. Narrowing `contents: write` to some smaller write scope would
preserve a premise that is false — that the job needs to write at all.

**Alternatives rejected.** Leaving the grant and documenting it as harmless — unused
authority is the thing least privilege is about; "harmless" is a property of today's step
list, not of the grant. Setting the repository-wide default token scope to read-only in
settings instead — correct and complementary, but it is a repository setting rather than a
reviewable file, so it cannot be asserted by a test or seen in a diff. Both, ideally; only
the in-repo half is in this card's power.

### Decision 4 — Immutable pins, plus the mechanism that keeps them from going stale

Every `uses:` reference is pinned to a full 40-character commit SHA with the readable
version retained as a trailing comment (`uses: actions/checkout@d23441a4… # v6.1.0`). The
Postgres tier's `postgres:16` becomes a `@sha256:` digest reference.

A tag is a mutable pointer. `actions/checkout@v6` re-resolves on every run, so the code
executing in CI — with whatever token scope that job holds — is whatever the tag points at
today, which is not the code anyone reviewed. The same argument applies to a container
image: `postgres:16` is rebuilt upstream on every 16.x patch and silently becomes a
different image. A SHA and a digest are the only immutable references the platform offers.
The version comment is not decoration: without it a pin is unreadable, and an unreadable
pin does not get updated, it gets replaced with a tag by the next person in a hurry.

Every SHA in this card was resolved against the upstream repository at authoring time
(`git ls-remote`), and the digest against the Docker Hub registry manifest API; the exact
queries are recorded in [`docs/builder/bld-049.md`][bld-049] so the next refresh is a
re-run rather than a re-derivation. **No SHA or digest in this card was constructed by
hand.** That constraint is worth stating because a fabricated pin fails in the most
expensive possible way — at some later unrelated CI run, looking like an infrastructure
outage.

**Immutability creates the opposite failure, and it must be answered in the same card.** A
pin that never moves also never picks up an upstream security fix; "immutable and stale" is
not an improvement on "mutable and current". The answer is the `github-actions` Dependabot
ecosystem in
[Decision 6](#decision-6--dependabot-over-a-scheduled-uv-upgrade-job), which rewrites both
the SHA and its trailing version comment. Pinning and automated updating are two halves of
one posture, and shipping either alone is a regression on the other axis.

**One honest limitation.** `google/osv-scanner-action` is SHA-pinned, but the action is a
Docker action whose own `action.yml` references its runtime image by the mutable tag
`ghcr.io/google/osv-scanner-action:v2.3.8`. Pinning our reference to a SHA fixes the
action definition — including which image tag it names — but the image behind that tag is
upstream's to rebuild. Closing the gap would require forking the action, which trades a
small mutability window for a permanent maintenance burden and a fork that itself goes
stale. Recorded rather than papered over; the SHA pin is what makes upstream's own
"behavior may change in a minor patch update" warning inapplicable to the definition.

### Decision 5 — `osv-scanner` against `uv.lock`, on a clock and on every resolution diff

The audit step is `osv-scanner`, invoked as `--lockfile=uv.lock`, in a new
`dependency-audit.yml` triggered on `pull_request` (paths-filtered to `uv.lock`,
`pyproject.toml`, and the workflow itself), on a daily `schedule`, and on
`workflow_dispatch`.

**Why `osv-scanner` over `pip-audit` and `safety`.** The deciding property is that
`osv-scanner` reads `uv.lock` **natively**, so the audited artifact is the exact resolution
this project builds, tests, and installs — no export step in between. That is not a
convenience argument in this repository, it is a correctness one: this lock carries **two
Django versions behind disjoint `python_full_version` markers** (`5.2.16` under `< 3.12`,
`6.0.7` under `>= 3.12`). `pip-audit` consumes a `requirements.txt` export or a live
environment, and either one flattens the marker-split resolution to a single environment —
which would have audited exactly one of the two Django versions and reported the other as
absent. An audit that silently covers half its input is worse than no audit, because it
reports success. `safety`'s current model routes its full vulnerability database through an
authenticated commercial account, which makes CI depend on a credential and a service tier
for something the OSV database provides openly.

Auditing `uv.lock` also satisfies the card's "production resolution + optional extras"
requirement with one scan target and no second invocation: `uv.lock` contains the
production resolution and every optional extra and dependency group in one file. The
compatibility environment is excluded structurally, per
[Decision 2](#decision-2--the-5-2-0-cell-is-a-compatibility-contract-not-a-deployment-target).

**Why both triggers.** They fail in opposite directions and neither is sufficient. A
PR-only audit cannot see a vulnerability published against a dependency that is already
locked — the case that actually caused **S6**, where no diff was pending and no one learned
anything. A schedule-only audit lets a vulnerable resolution merge first and reports it the
next morning. The pull-request trigger is paths-filtered because a PR that touches neither
`pyproject.toml` nor `uv.lock` cannot change the resolution, and an audit that runs on
every documentation PR is an audit people learn to scroll past.

**No SARIF upload, and therefore no `security-events: write`.** Upstream's recommended
reusable workflows report through the code-scanning API, which requires that scope. The
findings here are equally actionable from the job's exit status and log — the scanner exits
non-zero and prints the advisory table, which is what a failed check shows a reviewer. The
alternative buys a security-tab dashboard at the price of a write scope on every scheduled
run, plus a reusable workflow whose internal permissions and pins are outside this card's
review. Declining it keeps the entire audit workflow at `contents: read`, which is the
posture the rest of this card argues for. Calling the inner action directly also means the
`scan-args` are visible in this repository rather than inherited.

**Alternatives rejected.** `pip-audit` with a `uv export` step — flattens the marker-split
resolution, above. `safety` — credential and service-tier dependency. Upstream's reusable
workflow — needs `security-events: write` and hides its own pins. Running the audit as a
step inside `django.yml` — couples a supply-chain signal to the test matrix's own success
and makes the daily schedule impossible without also running the matrix.

### Decision 6 — Dependabot over a scheduled `uv lock --upgrade` job

Updates are delivered by `.github/dependabot.yml` covering two ecosystems: `uv` for Python
dependencies and `github-actions` for the workflow pins.

Dependabot's `uv` ecosystem reached general availability for version updates in March 2025
and gained security updates in December 2025; it resolves and rewrites `uv.lock` itself, so
an update PR lands the same artifact
[Decision 5](#decision-5--osv-scanner-against-uv-lock-on-a-clock-and-on-every-resolution-diff)'s
audit scans. Both facts were verified against GitHub's current documentation at authoring
time rather than assumed — the card flagged both as open questions precisely because the
ecosystem support is recent.

**Why not a scheduled `uv lock --upgrade` job**, which the card offered as the alternative
and which is genuinely tempting in a `uv`-native repository: it produces one opaque
"bump everything" commit with no upstream release notes, no per-dependency review boundary,
and no way to accept one update while holding another. It would also have to reimplement
the mapping from a published advisory to a specific upgrade — which is precisely the
service Dependabot's security updates already provide, wired to the same alerts stream a
maintainer sees. The `github-actions` ecosystem settles it regardless: nothing about
`uv lock` updates a pinned action SHA, so a `uv`-only upgrade job would leave
[Decision 4](#decision-4--immutable-pins-plus-the-mechanism-that-keeps-them-from-going-stale)'s
pins to rot and require a second mechanism anyway.

The dev-tooling group exists so that routine linter and pytest-plugin churn arrives as one
PR rather than crowding out the updates that change what consumers install. Grouping is
applied only to `minor` and `patch` development updates; anything that could change
behaviour for a consumer stays individually reviewable.

**Slice 4 adds one dev-group dependency, `pyyaml`.** The governance test parses workflow
YAML structurally, and no YAML parser is currently installed. It joins the dev group, never
`[project].dependencies` — consumers install nothing new — following the
[soft dependency][glossary-soft-dependency] entry's standing discipline that a dependency
gate adds the dev-group row and regenerates `uv.lock` in the same change. It needs no
[`require_optional_module`][glossary-require_optional_module] guard, because no package
module imports it; the import lives in a test.

**Alternatives rejected.** Scheduled `uv lock --upgrade` — above. Renovate — a superset of
what is needed here, at the cost of a third-party app installation and a second
configuration language, for a repository whose update surface is one lock file and five
actions. Regex-parsing the workflows in the governance test to avoid the `pyyaml`
dependency — trades a three-line dev-group addition for a hand-rolled parser that would
have to model YAML block structure to find job boundaries, and would be wrong in exactly
the cases worth catching.

### Decision 7 — Timeouts are per job, and sized by tier rather than uniformly

Every job gets `timeout-minutes`: 10 for `django.yml`'s lint job, 45 for its test matrix,
45 for the Postgres shards, and `kanban-pages.yml`'s existing 15 / 10 unchanged.

A timeout's job is to convert a hang into a failure. Its value therefore has to sit far
enough above the observed run time that a slow-but-healthy run is not killed, and far
enough below GitHub's six-hour default that a wedged runner is released promptly. Uniform
values fail on one side or the other: 10 minutes on the test matrix would kill legitimate
full-matrix runs, and 45 on the lint job would hold a runner for 44 minutes past the point
a `ruff` invocation could possibly still be working. The lint job installs and runs three
fast checks; the test and Postgres tiers install a Python, sync dependencies, and run the
suite under `xdist`.

These are deliberately generous rather than tight. A timeout tuned close to the current
run time becomes a flaky failure the first time a runner is slow, and a flaky gate gets
disabled — so the failure mode of a too-generous timeout (a wedged job held somewhat
longer) is strictly better than that of a too-tight one.

Reusable-workflow calls (`jobs.<id>.uses`) cannot carry `timeout-minutes`; the governance
test skips them for that reason rather than asserting something the platform forbids.

### Decision 8 — The governance posture is asserted by a test, not by review

`tests/test_ci_governance.py` parses every file in `.github/workflows/` plus
`.github/dependabot.yml` and asserts: each workflow is valid YAML with at least one job;
each declares exactly `permissions: {contents: read}` at the top level; no job grants
`contents: write`; every non-reusable job has a positive `timeout-minutes`; every external
`uses:` is pinned to a full 40-character SHA and carries a version comment; every
`actions/checkout` sets `persist-credentials: false`; every container image is
digest-pinned; Dependabot covers both ecosystems; and the audit workflow keeps both its
`pull_request` and `schedule` triggers.

The posture in Slice 2 is otherwise **structurally invisible to this repository**. Nothing
imports a workflow file, so a permission scope widening, a pin decaying to a tag, or a new
job landing with no timeout would every one of them pass a fully green suite. The
established local remedy for a governance rule with no runtime reachability is a repo-tool
test — `tests/test_clean_up.py` is the precedent — and this is the same shape.

The value it protects is specifically the *next* change, not this one. This card's diff is
reviewed; the workflow edit six months from now, made by someone who does not know why
`persist-credentials: false` is there, is what the test is for. Every assertion carries the
reason in its docstring for that reader.

It is placed in root `tests/` under the
[Live-first coverage mandate][glossary-live-first-coverage-mandate]'s
genuinely-unreachable-live clause: a workflow YAML file cannot be reached from a fakeshop
`/graphql/` request by any route. It adds **no coverage exposure** — coverage's source is
`django_strawberry_framework` only, and this module imports none of it, so `fail_under =
100` is unaffected.

The assertions were **verified to fail** against a deliberately regressed workflow (a tag
pin, a `contents: write` default, and a removed timeout each produced the expected
failure); the proof run is recorded in [`docs/builder/bld-049.md`][bld-049]. A governance
test that has never failed is indistinguishable from one that cannot.

**Alternatives rejected.** A pre-commit hook — runs only for people who installed it, and
this must hold for a web-UI edit. `actionlint` — a good complement that checks workflow
*syntax and expressions*, but it does not encode this project's permission and pin
policies, which are the thing at risk. OpenSSF Scorecard in CI — reports a score rather
than failing a build, and needs its own token scope.

### Decision 9 — Two comment conventions this card commits to in the workflows

The workflow comments this card adds carry a `spec-049 Decision N` pointer rather than
prose restating the rationale, matching the existing `spec-044 Decision 6` reference in
`django.yml`'s matrix comment. A workflow file is the wrong place to relitigate a decision
and the right place to name it.

Separately, the stale comment in `django.yml`'s Django-install step — which explained the
`--upgrade-package Django` behaviour by reference to "the locked 5.2.14" — is corrected to
`5.2.16` in the same change as the lock refresh. A comment that names a version is part of
that version's blast radius, and this card's Slice 1 is the change that moved it. Leaving
it would create the specific failure this repository has hit before: a downstream doc more
accurate than the thing it documents.

### Decision 10 — The version bump belongs to the `0.0.14` joint cut

This card does **not** move the version quintet. It targets `0.0.14`, sharing that patch
with cards 041-045 and with its three program siblings (046, 047, 048). The quintet —
`pyproject.toml [project].version`, `django_strawberry_framework/__init__.py::__version__`,
the `tests/base/test_init.py` assertion that pins them together, the glossary's
package-version line, and the package's own `version` entry in `uv.lock` — already reads
`0.0.14`, so there is no bump for this card to take.

Under the [Joint version cut][glossary-joint-version-cut] rule the release wording belongs
to the **last** card of a shared line to land. This card is the last of the four-card
program, so it is the natural owner of that wording — but the wording is the cut's, not
this slice's, and Slice 5 claims only the documentation fold-in.

## Implementation plan

| Slice | Files | Delta |
|---|---|---|
| 1 | `uv.lock` | Django `5.2.14` → `5.2.16` (`python_full_version < '3.12'`) and `6.0.5` → `6.0.7` (`>= '3.12'`); `cryptography` `49.0.0` → `50.0.0`; `pillow` `12.2.0` → `12.3.0` (and its `pyopenssl` transitive). `pyproject.toml` floors untouched. |
| 2 | `.github/workflows/django.yml` | Top-level `permissions: contents: read`; the `test` job's `contents: write` deleted; `timeout-minutes` 10 / 45; both checkouts SHA-pinned with `persist-credentials: false`; `compatibility_only` on the three `5.2.0` matrix rows plus the job-name suffix and the contract comment; the `5.2.14` → `5.2.16` comment correction. (**Amended 2026-08-05:** those three rows now force-install `Django==5.2.16`, the raised floor, and keep the labelling — see the amendment row below.) |
| 2 | `.github/workflows/postgres.yml` | Top-level `permissions: contents: read`; `timeout-minutes: 45`; checkout SHA-pinned with `persist-credentials: false`; `postgres:16` → `postgres@sha256:…` with the refresh-procedure comment. |
| 2 | `.github/workflows/kanban-pages.yml` | `checkout`, `configure-pages`, `upload-pages-artifact`, `deploy-pages` SHA-pinned with version comments; `persist-credentials: false` on the checkout. Permissions and timeouts already correct. |
| 3 | `.github/workflows/dependency-audit.yml` (new) | `pull_request` (paths-filtered) + daily `schedule` + `workflow_dispatch`; `permissions: contents: read`; `concurrency` group; `timeout-minutes: 15`; SHA-pinned checkout and `osv-scanner-action` with `--lockfile=uv.lock`. |
| 3 | `.github/dependabot.yml` (new) | `uv` and `github-actions` ecosystems, weekly, `open-pull-requests-limit: 5`, commit-message prefixes, and the dev-tooling group. |
| 4 | `tests/test_ci_governance.py` (new) | The eleven assertions in [Decision 8](#decision-8--the-governance-posture-is-asserted-by-a-test-not-by-review), parametrized per workflow file. |
| 4 | `pyproject.toml` | The `pyyaml>=6.0.2` dev-group row and its rationale comment. |
| 5 | `docs/GLOSSARY.md` (DB), `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, `KANBAN.md` (DB) | Fold-in and the secure-version note. |
| — | **Amendment (2026-08-05)** — `pyproject.toml`, `uv.lock`, `.github/workflows/django.yml`, `.github/workflows/postgres.yml`, `tests/test_ci_governance.py` | Post-card, by maintainer decision: the declared Django floor becomes `Django>=5.2.16`; the exact-floor matrix cell force-installs `Django==5.2.16` and keeps its `compatibility_only` key, `[compatibility floor]` job-name suffix, and contract comment; the governance test tracks the raised floor. Not part of what card 049 built — recorded here so the row-2 delta above is not read as live. |

## Helper-reuse obligations (DRY)

- **One audit tool and one scan target.** `osv-scanner` against `uv.lock` is the only
  vulnerability audit in the repository. A second tool, or a second invocation over an
  exported requirements file, would produce two findings lists that disagree and two places
  to suppress.
- **One place per action pin.** Each action appears with its SHA and version comment at its
  `uses:` site and nowhere else; no `env` indirection, no repeated SHA constant. Dependabot
  rewrites `uses:` lines, so a pin held anywhere else silently stops being updated.
- **One governance test module** owns every workflow assertion. A per-workflow test file
  would duplicate the loader and drift; the module parametrizes over the glob instead, so a
  new workflow file is covered the moment it lands rather than when someone remembers.
- **One loader helper** (`_load`) and one job/step accessor pair (`_jobs`, `_steps`) inside
  that module. No assertion re-opens a file or re-implements the `None`-tolerant traversal
  that YAML's empty-mapping cases require.
- **One immutability rule, expressed once** as the `FULL_SHA` pattern. Both the SHA
  assertion and the version-comment assertion consult it rather than each spelling out
  "40 hex characters".
- **The version quintet stays one list.** Slice 5 moves the same five sites the
  [Joint version cut][glossary-joint-version-cut] entry enumerates; no sixth site learns
  the version.

## Edge cases and constraints

- **A job-level `permissions` block replaces, not merges.** `kanban-pages.yml`'s `deploy`
  job must therefore keep restating `contents: read` alongside its `id-token: write` /
  `pages: write`. Dropping the restatement to "inherit" the default would revoke read
  access, not add to it.
- **A reusable-workflow call cannot carry `timeout-minutes`.** The governance test skips
  jobs with a `uses:` key rather than asserting a platform-forbidden field. This repository
  currently has no such job; the branch exists so that adding one does not present as a
  governance regression.
- **`yaml.safe_load` parses the `on:` key as the boolean `True`** under YAML 1.1's
  truthiness rules. The audit-trigger assertion reads `workflow[True]` with a `workflow["on"]`
  fallback rather than assuming either spelling.
- **Comments must be stripped before matching image references.** The Postgres comment
  block names the `postgres:16` tag in prose while the `docker run` line is digest-pinned;
  matching raw text would flag the explanation as the violation. This was an observed
  failure of the first draft of that assertion, not a hypothetical.
- **A workflow directory with no files** would make the parametrized assertions vacuously
  true. The collection helper asserts non-empty at import.
- **`persist-credentials: false` is safe only because nothing pushes.** If a future job
  needs to push, it sets `persist-credentials: true` on its own checkout and the governance
  test must be amended in the same change — the assertion is the place that conversation is
  forced to happen.
- **The digest pin does not float across Postgres minor versions.** `postgres@sha256:…` is
  one image, so a `16.x` upstream patch requires a deliberate digest refresh. That is the
  intent; the refresh query is recorded in [`docs/builder/bld-049.md`][bld-049].
- **The audit's `pull_request` paths filter means most PRs never run it.** A PR that cannot
  change the resolution has nothing to audit; the daily schedule is what covers the
  resolution itself.
- **The audit is expected to fail closed on a new advisory.** A non-zero scanner exit fails
  the job by design. There is no `continue-on-error`, because a supply-chain finding that
  does not block is a notification, and this repository already demonstrated that
  notifications nobody receives are how **S6** happened.

## Test plan

| Tier | Row | Asserts |
|---|---|---|
| `tests/` | `test_workflow_parses` (per workflow) | Every workflow is a YAML mapping declaring at least one job. |
| `tests/` | `test_workflow_declares_top_level_read_only_permissions` (per workflow) | Top-level `permissions` is exactly `{contents: read}`. |
| `tests/` | `test_no_job_grants_repository_write` (per workflow) | No job's `permissions.contents` is `write`. |
| `tests/` | `test_every_job_declares_a_timeout` (per workflow) | Every non-reusable job has a positive integer `timeout-minutes`. |
| `tests/` | `test_every_external_action_is_pinned_to_a_full_commit_sha` (per workflow) | Every non-local `uses:` ref matches 40 hex characters. |
| `tests/` | `test_pinned_actions_keep_a_readable_version_comment` (per workflow) | Every SHA-pinned `uses:` line carries a `#` comment. |
| `tests/` | `test_checkout_steps_do_not_persist_credentials` (per workflow) | Every `actions/checkout` step sets `persist-credentials: false`. |
| `tests/` | `test_container_images_are_pinned_by_digest` | Every image reference in executable (comment-stripped) workflow text uses `@sha256:`. |
| `tests/` | `test_dependabot_covers_python_and_github_actions` | `dependabot.yml` covers both the `uv` and `github-actions` ecosystems. |
| `tests/` | `test_dependency_audit_workflow_runs_on_pull_request_and_a_schedule` | Both triggers are present. |
| Command | `uv lock --check` | The refreshed lock is a valid resolution of the unchanged floors. |
| Command | `osv-scanner --lockfile=uv.lock` | Exits 0 against the refreshed lock (it exited 1 with 14 findings before Slice 1). |
| Command | `uv run pytest` | The full suite passes at `fail_under = 100`, proving the lock refresh changed no behaviour. |

**Failability.** Each structural assertion was confirmed to fail against a regressed
workflow rather than merely to pass against the current one — see
[Decision 8](#decision-8--the-governance-posture-is-asserted-by-a-test-not-by-review) and
[`docs/builder/bld-049.md`][bld-049].

**What cannot be proven locally.** "CI green" is a statement about GitHub's runners. The
local substitutes are the three commands above plus the structural parse of every workflow;
the scheduled trigger, the Dependabot ecosystem resolution, and the runner-side behaviour of
each newly-pinned action SHA are observable only after the change lands. Recorded as such
rather than claimed.

## Doc updates

Slice 5, all of it fold-in rather than new surface:

- `README.md` — the supported-versions prose gains the secure-version sentence: the
  `django>=5.2` floor is an API-compatibility floor, and production consumers must install
  the newest patch in their supported Django series.
- `docs/README.md` — the same secure-version note beside the version table, and the
  "Shipped today" move.
- **Amendment (2026-08-05):** the secure-version statement is written against the raised
  `Django>=5.2.16` floor and lands in `docs/README.md`'s
  [Production security profile][docs-readme-production-profile] — the section a deployment
  review actually walks — with a condensed mirror in [`SECURITY.md`][security] beside its
  supported-versions table. `README.md` carries no dependency-floor prose to attach it to.
- `docs/GLOSSARY.md` (DB-rendered) — the secure-version statement folded into the
  [Hard dependency][glossary-hard-dependency]
  entry, whose subject is exactly the unconditionally-installed packages this concerns. No
  new term.
- `docs/TREE.md` (script-rendered) — regenerated for `tests/test_ci_governance.py`.
- `TODAY.md` — the capability snapshot, and the security-remediation program recorded as
  complete now that card 4 of 4 lands.
- `KANBAN.md` (DB-rendered) — the card to Done and its `SpecDoc`.
- `CHANGELOG.md` — **not** touched; the `0.0.14` entry is the maintainer's per
  [`AGENTS.md`][agents].

`docs/GLOSSARY.md`, `docs/TREE.md`, and `KANBAN.md` are generated. Their edits are made in
the source (the fakeshop glossary / kanban DB, or the module docstrings) and re-rendered,
never by hand.

## Risks and open questions

- **Dependabot's `uv` lockfile handling has open upstream issues.** Reports exist of update
  PRs that move `pyproject.toml` without regenerating `uv.lock`, or the reverse. Preferred
  answer for `0.0.14`: ship the `uv` ecosystem anyway, because the audit in
  [Decision 5](#decision-5--osv-scanner-against-uv-lock-on-a-clock-and-on-every-resolution-diff)
  reads `uv.lock` directly and would fail on a PR that left it stale — the two mechanisms
  check each other. Fallback if the PRs prove unusable: keep the `github-actions` ecosystem,
  drop the `uv` one, and add a scheduled `uv lock --upgrade-package` job per
  [Decision 6](#decision-6--dependabot-over-a-scheduled-uv-upgrade-job)'s rejected
  alternative.
- **The pinned action SHAs are unexercised until CI runs.** Each was resolved from the
  upstream tag it replaces, so each should be a no-op, but a mis-resolved SHA fails as an
  infrastructure error rather than a test failure. Preferred answer: the first `main` run
  after the merge is the verification, and the version comments make a bad pin a one-line
  revert. Fallback: revert the single offending pin to its tag and re-resolve.
- **`osv-scanner`'s inner image tag is mutable**, per
  [Decision 4](#decision-4--immutable-pins-plus-the-mechanism-that-keeps-them-from-going-stale).
  Preferred answer: accept and record, since the action definition is pinned. Fallback if a
  supply-chain incident touches that image: pin `ghcr.io/google/osv-scanner-action` by
  digest via a fork, accepting the maintenance cost then rather than now.
- **The daily audit will eventually fail on an advisory with no fixed version available.**
  Preferred answer for `0.0.14`: handle it as it arises, since the correct response depends
  entirely on whether the affected package is a
  [hard dependency][glossary-hard-dependency], a
  [soft dependency][glossary-soft-dependency], or dev-only. Fallback if it becomes routine:
  an `osv-scanner` ignore file with a mandatory expiry date per entry — never an
  open-ended suppression.
- **`pyyaml` is a new dev-group dependency for a governance test.** Preferred answer:
  accept, per [Decision 6](#decision-6--dependabot-over-a-scheduled-uv-upgrade-job) — a
  hand-rolled YAML parser would be wrong precisely where the assertions matter. Fallback if
  the dev group must shrink: none needed; `pyyaml` is a transitive dependency of much of the
  Python tooling ecosystem already.
- **A repository-level default token scope would strengthen
  [Decision 3](#decision-3--least-privilege-is-a-default-plus-a-visible-exception-not-a-per-job-audit)**
  but is a settings change, not a file. Preferred answer: the maintainer sets the default
  workflow permissions to read-only in repository settings; the in-repo blocks make that
  change a no-op rather than a behaviour change, so the order is safe either way.
- **Timeout values are estimates, not measurements** — sized generously per
  [Decision 7](#decision-7--timeouts-are-per-job-and-sized-by-tier-rather-than-uniformly).
  Preferred answer: leave them until a real run distribution exists. Fallback: tighten
  against observed p95 once the matrix has history, never below 2x observed.

## Out of scope (explicitly tracked elsewhere)

- Secure output and error defaults (S5, S8, S10) — shipped in [`spec-048`][spec-048].
- The execution resource policy (S3, S4) — shipped in [`spec-047`][spec-047].
- Transport security (S1, S2, S9, S11) — shipped in [`spec-046`][spec-046].
- Extracting the debug extension into its own distribution —
  [`TODO-ALPHA-050-0.0.19`][kanban], which removes `extensions/debug.py` and will change
  the dependency surface this card's audit reads.
- Artifact signing, provenance attestation, and SLSA build levels — not carded. A publish
  workflow is the natural home and none exists yet.
- A self-hosted package mirror or private registry posture — not carded.
- OpenSSF Scorecard reporting in CI — considered and rejected in
  [Decision 8](#decision-8--the-governance-posture-is-asserted-by-a-test-not-by-review);
  not carded.
- Raising the declared dependency floors — deliberately refused by
  [Decision 1](#decision-1--the-lock-moves-the-declared-floors-do-not), not deferred.
  **Amendment (2026-08-05):** refused here, then done anyway by maintainer decision for
  Django alone (`Django>=5.2.16`). Recorded as a reversal of this card's refusal, not as a
  scope item it quietly carried.

## Definition of done

- [ ] `uv.lock` resolves Django `>= 5.2.16` under `python_full_version < '3.12'` and
      `>= 6.0.7` under `>= '3.12'`; `uv lock --check` passes; `pyproject.toml`'s
      `[project].dependencies` floors are byte-identical to their pre-card state
      (**amended 2026-08-05**: the Django floor has since moved to `>=5.2.16`; the byte-identity
      claim describes this card's own delivery, not the current file).
- [ ] `osv-scanner --lockfile=uv.lock` exits 0 against the refreshed lock, with no
      ignore-list and no suppression file anywhere in the repository.
- [ ] Every workflow declares `permissions: contents: read` at the top level; no job grants
      `contents: write`; the only job-level elevation in the repository is
      `kanban-pages.yml`'s `deploy` (`id-token: write` / `pages: write`).
- [ ] Every `uses:` reference is a full 40-character commit SHA carrying a readable
      `# vX.Y.Z` comment, and every SHA was resolved from upstream rather than constructed;
      the Postgres image is pinned by `@sha256:` digest.
- [ ] Every `actions/checkout` sets `persist-credentials: false`; every job declares a
      positive `timeout-minutes`.
- [ ] The exact-Django-5.2.0 matrix cell still runs, still force-installs
      `strawberry-graphql==0.316.0`, and is labelled compatibility-only in its job name, its
      matrix comment, and `README.md`; it is not an input to the audit.
- [ ] **Amendment (2026-08-05)** — restated for the raised floor: `pyproject.toml` declares
      `Django>=5.2.16`; the exact-floor matrix cell force-installs `Django==5.2.16` (not
      `5.2.0`) alongside `strawberry-graphql==0.316.0`, keeps its `[compatibility floor]`
      job-name label and contract comment, and is still not an input to the audit; no
      supported configuration resolves Django below `5.2.16`.
- [ ] `.github/workflows/dependency-audit.yml` runs on `pull_request`, on a `schedule`, and
      on `workflow_dispatch`, at `contents: read`, with no SARIF upload and no
      `security-events` scope.
- [ ] `.github/dependabot.yml` covers the `uv` and `github-actions` ecosystems.
- [ ] `tests/test_ci_governance.py` asserts the whole posture, was proven to fail against a
      regressed workflow, and adds no package coverage surface.
- [ ] No file under `django_strawberry_framework/` is modified and the generated SDL is
      unchanged.
- [ ] Full suite green at `fail_under = 100` for `django_strawberry_framework`; `ruff
      format --check`, `ruff check`, and `scripts/check_trailing_commas.py --check` all
      clean.
- [ ] Docs folded in with the secure-version note; the version quintet rides the joint
      `0.0.14` cut.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[kanban]: ../KANBAN.md
[security]: ../SECURITY.md

<!-- docs/ -->
[docs-readme-production-profile]: README.md#production-security-profile
[feedback2]: feedback2.md
[glossary]: GLOSSARY.md
[glossary-hard-dependency]: GLOSSARY.md#hard-dependency
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-per-operation-extension-isolation]: GLOSSARY.md#per-operation-extension-isolation
[glossary-require_optional_module]: GLOSSARY.md#require_optional_module
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency

<!-- docs/SPECS/ -->
[spec-046]: SPECS/spec-046-transport_security-0_0_14.md
[spec-047]: SPECS/spec-047-resource_policy-0_0_14.md
[spec-048]: SPECS/spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->
[bld-049]: builder/bld-049.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
