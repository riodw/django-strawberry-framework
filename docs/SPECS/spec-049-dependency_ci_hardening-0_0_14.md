# Spec: Dependency and CI hardening — keep the lock current, audit the resolution on a clock, run CI at least privilege

Targeted at `0.0.14` (card [`DONE-049-0.0.14`][kanban]), one of four security cards on that
line beside [`spec-046`][spec-046] (transport security), [`spec-047`][spec-047] (the
execution resource policy), and [`spec-048`][spec-048] (secure output and error defaults).

**This card owns no package source.** Nothing under `django_strawberry_framework/` belongs to
it, it adds no settings key, and it does not touch the generated SDL. Its surface is the
dependency lock, the workflow files under `.github/workflows/`, `.github/dependabot.yml`,
`osv-scanner.toml`, and one governance test. The other three cards change what the package
*does*; this one governs what the project *ships and proves*, and a governance card that grows
a source diff is one nobody can review.

Status: **SHIPPED — all five slices are built and released.** The `Status:` line is the
completion source of truth (the shipped-spec convention); the Slice checklist boxes below
stay unticked.

**Version boundary** (see
[Decision 10](#decision-10--the-version-bump-belongs-to-the-joint-cut)): this card owns
no version state.

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [Hard dependency][glossary-hard-dependency] — the unconditionally-installed packages whose
  locked versions the lock tracks and whose declared floors are API-compatibility bounds,
  never secure-version recommendations. The secure-version statement lives in this entry.
- [Soft dependency][glossary-soft-dependency] — the optional-extra architecture.
  `cryptography` is a soft dependency real consumers install, so its lock entry is
  consumer-facing surface the audit covers; the dev-group-row-plus-lock-regeneration
  discipline is the one the `pyyaml` row follows.
- [`require_optional_module`][glossary-require_optional_module] — the single optional-import
  owner; named to make explicit that this card adds no optional-import surface.
- [Per-operation extension isolation][glossary-per-operation-extension-isolation] — one of
  the reasons for the `strawberry-graphql` floor the exact-floor matrix cell force-installs,
  and therefore part of why that cell exists.
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the test-placement
  rule that puts the governance test in root `tests/`: a workflow YAML file is not
  reachable from a fakeshop `/graphql/` request by any route.
- [Joint version cut][glossary-joint-version-cut] — the release rule whose "`uv.lock`
  **dependency** entries are not version state" clause lets lock refreshes land on their own.

This spec adds no glossary term. It ships no consumer-visible symbol, so there is nothing
for the capability catalogue to describe.

## Slice checklist

Each top-level item maps to one commit / PR.

- [ ] **Slice 1 — the lock tracks the top of the audited range**
      `uv.lock` resolves Django twice behind disjoint `python_full_version` markers (a
      `5.2.x` patch below `3.12`, the newest series at `>= 3.12`) and keeps every locked
      package off known advisories. The declared floors in `pyproject.toml` are a separate
      statement ([Decision 1](#decision-1--the-lock-tracks-the-top-of-the-range-the-declared-floor-is-a-compatibility-bound)).
- [ ] **Slice 2 — least-privilege CI**
      Every workflow under `.github/workflows/` declares top-level
      `permissions: contents: read`; no job grants `contents: write`;
      `persist-credentials: false` on every checkout; every `uses:` pinned to a full commit
      SHA with a readable version comment; the Postgres image pinned by digest;
      `timeout-minutes` on every job. The exact-floor Django cell is labelled
      compatibility-only
      ([Decision 2](#decision-2--the-exact-floor-cell-is-a-compatibility-contract-not-a-deployment-target)).
- [ ] **Slice 3 — audit and update automation**
      `.github/workflows/dependency-audit.yml`: `osv-scanner` against `uv.lock` on pull
      requests, on a daily schedule, and on dispatch, with `osv-scanner.toml` holding only
      expiring, reasoned exemptions. `.github/dependabot.yml`: the `uv` and
      `github-actions` ecosystems.
- [ ] **Slice 4 — the governance test**
      `tests/test_ci_governance.py` asserts the Slice 2 and Slice 3 posture structurally;
      `pyproject.toml` carries the `pyyaml` dev-group row it needs.
- [ ] **Slice 5 — docs fold-in**
      The secure-version statement in `docs/README.md`'s
      [Production security profile][docs-readme-production-profile], [`SECURITY.md`][security],
      and the [Hard dependency][glossary-hard-dependency] glossary entry; `docs/TREE.md` and
      `KANBAN.md` regenerated.

## Problem statement

Two independent gaps, both in the project's supply chain rather than its code.

**A resolved dependency graph goes stale, and nothing reports it.** A lock file is stale the
moment it is written: upstream keeps publishing security releases, and a vulnerability is
published against a version already locked without anyone touching the repository. Without
an audit command, a scheduled security workflow, and an update configuration, the project
has no way to learn this, and a hand refresh only restores the same condition tomorrow.
Soft dependencies such as `cryptography` are consumer-facing surface, not merely test
scaffolding, so their lock entries matter as much as Django's.

**CI can run with more authority than it uses, and less determinism than it needs.** Four
distinct exposures:

- A job-level `contents: write` grant extends unused authority to every step in the job,
  including every third-party action and the entire installed dependency tree.
- `actions/checkout` persists its credential into `.git/config` by default, leaving a
  usable token in the workspace for all subsequent steps. No job in this repository pushes,
  so the credential has no consumer.
- A mutable action tag or container tag (`actions/checkout@vN`, `postgres:16`) executes
  whatever the reference points at on the day of the run, which is not a thing anyone
  reviewed.
- A job without `timeout-minutes` holds a runner until GitHub's six-hour default when a
  download hangs or a test deadlocks.

## Goals

- The locked resolution sits at the top of the audited range on each Python marker, and no
  locked package carries a known advisory outside a reasoned, expiring exemption.
- A vulnerability published against an already-locked dependency surfaces without anyone
  touching the repository.
- An update path keeps immutable pins current instead of merely immutable.
- Every CI job holds the narrowest token scope that lets it do its work, executes only
  reviewed action code and container images, and bounds its own wall-clock time.
- The distinction between *compatibility support* and *secure-deployment support* is stated
  where it can be acted on: the declared `Django>=5.2.16` floor does not read as a security
  recommendation, because the next Django security release moves past it.
- The posture is asserted by a test, so it degrades loudly rather than silently.

## Non-goals

- No package source file, generated SDL, or settings key.
- No SARIF upload to the code-scanning API, and therefore no `security-events: write`
  anywhere ([Decision 5](#decision-5--osv-scanner-against-uvlock-on-a-clock-and-on-every-resolution-diff)).
- No self-hosted mirror, private registry, or artifact-signing posture. Out of scope and
  uncarded.

## Borrowing posture

There is no upstream primitive to borrow here: `graphene-django` and
`strawberry-graphql-django` publish packages, not a CI governance contract, and neither ships
a surface this card could adapt. The DRF-shape argument that governs the rest of the package
does not reach a workflow file.

The reference points are external and general: GitHub's documented hardening guidance for
Actions (least-privilege `permissions`, actions pinned to a full commit SHA,
`persist-credentials: false` on checkouts that do not push) and the OpenSSF Scorecard checks
that mechanize it (`Token-Permissions`, `Pinned-Dependencies`). Every posture item in Slice 2
maps to one of those; they are the checks a downstream consumer auditing this project will
actually run.

## User-facing API

None. This card adds no importable symbol, no `Meta` key, no settings key, and no schema
change; the entire delivery is governance configuration plus one test.

The consumer-facing output is a **security statement**: `Django>=5.2.16` in `pyproject.toml`
is the floor at which this package's API is compatible and the oldest Django it supports
(`5.2.0`–`5.2.15` are unsupported), and it is **not** a statement that `5.2.16` is safe to
deploy. Production consumers install the newest patch release in their supported Django
series. The statement lives in the user guide's
[Production security profile][docs-readme-production-profile] and, condensed, in
[`SECURITY.md`][security]'s deployment-hardening section. See
[Decision 2](#decision-2--the-exact-floor-cell-is-a-compatibility-contract-not-a-deployment-target).

## Architectural decisions

### Decision 1 — The lock tracks the top of the range; the declared floor is a compatibility bound

`uv.lock` tracks the top of the audited range; `pyproject.toml`'s `[project].dependencies`
floors move only for a compatibility or support reason.

The two express different things, and conflating them is the error available here. A
declared floor answers "below which version does this package's API stop working, and which
versions does the project support?" — for Django that is `5.2.16`, a support boundary that
deliberately coincides with a patched release (the one carrying the CVE-2026-48588 fix), and
the exact-floor matrix cell is the evidence. A lock entry answers "which version does this
project build, test, and install today?" — and that must be the newest audited release,
always. Deriving a floor from a security preference alone would break every consumer pinned
to a supported-but-older patch while doing nothing for the consumer who resolves Django
independently of this lock file — which is every consumer, because a library's lock file is
not installed. A floor is a point-in-time statement; the next security release makes it
older than the newest patch again.

The lock tracks the top of the range, not a version frozen when it was last edited, because
every unpinned CI node resolves from the lock: a stale lock turns each such node into a
second floor run and silences the top-of-range tripwires (`django.yml`'s Strawberry-install
step comment names the WebSocket handler read-set check in `tests/test_routers.py` as one).
Dependabot's weekly `uv` PR is what moves it
([Decision 6](#decision-6--dependabot-over-a-scheduled-uv-lock---upgrade-job)).

The [Joint version cut][glossary-joint-version-cut] entry draws the same line from the
release side: "`uv.lock` **dependency** entries are not version state."

**Alternatives rejected.** Pinning exact versions in `[project].dependencies` — makes the
package un-co-installable, the standard library anti-pattern. A blanket audit ignore-list
for advisories that have a fixed release — suppression, not remediation.

### Decision 2 — The exact-floor cell is a compatibility contract, not a deployment target

The exact-floor matrix nodes in `django.yml` install `Django==5.2.16` on Python `3.10` and
force-install `strawberry-graphql` at its declared floor (`0.322.2`). Push and pull-request
runs carry the single-DB node; manual dispatch adds the multi-DB one. Each carries a
`compatibility_only: "1"` matrix key, which renders a `[compatibility floor]` suffix into the
job name, and the matrix comment states what the cell does and does not assert.

The cell earns its place: an advertised floor with no test is a guess. It is also the only
node that runs the Strawberry floor, so it is simultaneously the evidence for that floor,
which [Per-operation extension isolation][glossary-per-operation-extension-isolation] is one
reason for.

A green tick on the floor cell sits next to a version that the next Django security release
will leave behind, and an adjacent green tick is exactly how a reader concludes a version is
endorsed. **Compatibility support and secure-deployment support are different contracts**,
and the cell says which one it is wherever a reader meets it: the rendered job name, the
matrix comment, and [`SECURITY.md`][security]. The comment states the prohibitions
positively — this cell must never be cited as a supported deployment target, copied into a
deployment example, or used to argue that pinning the floor exactly is a safe deployment
choice.

The cell is also, deliberately, **not audited**. The audit's scan target is `uv.lock`
([Decision 5](#decision-5--osv-scanner-against-uvlock-on-a-clock-and-on-every-resolution-diff)),
and the floor environment is constructed by a `uv pip install` override inside a job step —
it is not part of any resolution the audit reads. The separation is structural rather than a
suppression rule: there is no exemption to forget to remove, because the compatibility
environment was never in the audit's input.

**Alternatives rejected.** Dropping the cell — abandons the Django and Strawberry floor
tests to fix a labelling problem. Adding the floor environment to the audit with an
ignore-list — a permanent suppression that would mask a genuinely new advisory against that
environment.

### Decision 3 — Least privilege is a default plus a visible exception, not a per-job audit

Every workflow declares `permissions: contents: read` at the top level, and no job grants
`contents: write`.

A job-level `permissions` block **replaces** the workflow default rather than merging with
it, which is the property that makes this shape work: the top-level block sets the floor
for every job, and any job needing more must restate its entire scope in one place, next to
the step that consumes it. A reader looking for elevated authority greps for `permissions:`
at job level and finds a complete list — in this repository, exactly one entry,
`kanban-pages.yml`'s `deploy` job with `id-token: write` / `pages: write`, a genuine
requirement of OIDC-authenticated Pages deployment.

The `test` job inherits the default. Its only token consumer is the Coveralls upload, which
authenticates a coverage report against Coveralls' API with `GITHUB_TOKEN` from the step env
and never writes to the repository.

**Alternatives rejected.** A write grant documented as harmless — unused authority is the
thing least privilege is about; "harmless" is a property of today's step list, not of the
grant. Setting the repository-wide default token scope to read-only in settings instead —
correct and complementary, but a repository setting rather than a reviewable file, so it
cannot be asserted by a test or seen in a diff. Both, ideally; only the in-repo half is in
this card's power.

### Decision 4 — Immutable pins, plus the mechanism that keeps them from going stale

Every `uses:` reference is pinned to a full 40-character commit SHA with the readable
version retained as a trailing comment (`uses: actions/checkout@<sha> # vX.Y.Z`). The
Postgres tier starts `postgres@sha256:<digest>`.

A tag is a mutable pointer. `actions/checkout@vN` re-resolves on every run, so the code
executing in CI — with whatever token scope that job holds — is whatever the tag points at
today. The same argument applies to a container image: `postgres:16` is rebuilt upstream on
every 16.x patch and silently becomes a different image. A SHA and a digest are the only
immutable references the platform offers. The version comment is not decoration: without it
a pin is unreadable, and an unreadable pin does not get updated, it gets replaced with a tag
by the next person in a hurry.

**No SHA or digest is constructed by hand.** Each is resolved from upstream (`git ls-remote`
for an action tag, the Docker Hub registry manifest API for an image). A fabricated pin
fails in the most expensive possible way — at some later unrelated CI run, looking like an
infrastructure outage.

**Immutability creates the opposite failure, and it is answered in the same card.** A pin
that never moves also never picks up an upstream security fix. The answer is the
`github-actions` Dependabot ecosystem in
[Decision 6](#decision-6--dependabot-over-a-scheduled-uv-lock---upgrade-job), which rewrites both
the SHA and its trailing version comment. Pinning and automated updating are two halves of
one posture.

**One limitation.** `google/osv-scanner-action` is SHA-pinned, but it is a Docker action
whose own `action.yml` references its runtime image by a mutable tag. Pinning our reference
fixes the action definition — including which image tag it names — but the image behind that
tag is upstream's to rebuild. Closing the gap would require forking the action, which trades
a small mutability window for a permanent maintenance burden and a fork that itself goes
stale. The SHA pin is what makes upstream's own "behavior may change in a minor patch
update" warning inapplicable to the definition.

### Decision 5 — `osv-scanner` against `uv.lock`, on a clock and on every resolution diff

The audit step is `osv-scanner`, invoked as `--lockfile=uv.lock`, in `dependency-audit.yml`,
triggered on `pull_request` (paths-filtered to the workflow itself, `osv-scanner.toml`,
`pyproject.toml`, and `uv.lock`), on a daily `schedule`, and on `workflow_dispatch`.

**Why `osv-scanner` over `pip-audit` and `safety`.** `osv-scanner` reads `uv.lock`
**natively**, so the audited artifact is the exact resolution this project builds, tests,
and installs — no export step in between. That is a correctness argument in this repository:
the lock carries **two Django versions behind disjoint `python_full_version` markers**.
`pip-audit` consumes a `requirements.txt` export or a live environment, and either one
flattens the marker-split resolution to a single environment — auditing one of the two
Django versions and reporting the other as absent. An audit that silently covers half its
input is worse than no audit, because it reports success. `safety`'s model routes its full
vulnerability database through an authenticated commercial account, which makes CI depend on
a credential and a service tier for something the OSV database provides openly.

Auditing `uv.lock` covers the production resolution and every optional extra and dependency
group with one scan target and no second invocation. The compatibility environment is
excluded structurally, per
[Decision 2](#decision-2--the-exact-floor-cell-is-a-compatibility-contract-not-a-deployment-target).

**Exemptions expire.** `osv-scanner.toml` beside `uv.lock` is the only suppression file. Each
`[[IgnoredVulns]]` entry names one advisory, a `reason` stating why the lock cannot carry the
fix (for example, no fixed release exists for a supported Python marker), and an
`ignoreUntil` date after which the audit fails on it again so the exemption is re-decided.
An open-ended suppression is never written.

**Why both triggers.** They fail in opposite directions and neither is sufficient. A PR-only
audit cannot see a vulnerability published against a dependency that is already locked,
where no diff is pending and no one learns anything. A schedule-only audit lets a vulnerable
resolution merge first and reports it the next morning. The pull-request trigger is
paths-filtered because a PR that touches none of those files cannot change the resolution or
the exemptions, and an audit that runs on every documentation PR is one people learn to
scroll past.

**No SARIF upload, and therefore no `security-events: write`.** Upstream's recommended
reusable workflows report through the code-scanning API, which requires that scope. The
findings here are equally actionable from the job's exit status and log — the scanner exits
non-zero and prints the advisory table. The alternative buys a security-tab dashboard at the
price of a write scope on every scheduled run, plus a reusable workflow whose internal
permissions and pins are outside this card's review. Declining it keeps the audit workflow
at `contents: read`. Calling the inner action directly also keeps the `scan-args` visible in
this repository rather than inherited.

**Alternatives rejected.** `pip-audit` with a `uv export` step — flattens the marker-split
resolution, above. `safety` — credential and service-tier dependency. Upstream's reusable
workflow — needs `security-events: write` and hides its own pins. Running the audit as a
step inside `django.yml` — couples a supply-chain signal to the test matrix's own success
and makes the daily schedule impossible without also running the matrix.

### Decision 6 — Dependabot over a scheduled `uv lock --upgrade` job

Updates are delivered by `.github/dependabot.yml` covering two ecosystems: `uv` for Python
dependencies and `github-actions` for the workflow pins, both weekly with
`open-pull-requests-limit: 5` and per-ecosystem commit-message prefixes.

Dependabot's `uv` ecosystem resolves and rewrites `uv.lock` itself, so an update PR lands
the same artifact
[Decision 5](#decision-5--osv-scanner-against-uvlock-on-a-clock-and-on-every-resolution-diff)'s
audit scans.

**Why not a scheduled `uv lock --upgrade` job**: it produces one opaque "bump everything"
commit with no upstream release notes, no per-dependency review boundary, and no way to
accept one update while holding another. It would also have to reimplement the mapping from
a published advisory to a specific upgrade — the service Dependabot's security updates
already provide, wired to the same alerts stream a maintainer sees. The `github-actions`
ecosystem settles it regardless: nothing about `uv lock` updates a pinned action SHA, so a
`uv`-only upgrade job would leave
[Decision 4](#decision-4--immutable-pins-plus-the-mechanism-that-keeps-them-from-going-stale)'s
pins to rot and require a second mechanism anyway.

The `dev-tooling` group exists so that routine linter and pytest-plugin churn arrives as one
PR rather than crowding out the updates that change what consumers install. Grouping is
applied only to `minor` and `patch` development updates; anything that could change
behaviour for a consumer stays individually reviewable.

**The governance test needs `pyyaml`.** It parses workflow YAML structurally, so
`pyyaml>=6.0.2` is a dev-group row, never a `[project].dependencies` one — consumers install
nothing new — following the [soft dependency][glossary-soft-dependency] entry's discipline
that a dependency gate adds the dev-group row and regenerates `uv.lock` in the same change.
It needs no [`require_optional_module`][glossary-require_optional_module] guard, because no
package module imports it; the import lives in a test.

**Alternatives rejected.** Scheduled `uv lock --upgrade` — above. Renovate — a superset of
what is needed here, at the cost of a third-party app installation and a second
configuration language, for a repository whose update surface is one lock file and a handful
of actions. Regex-parsing the workflows in the governance test to avoid the `pyyaml`
dependency — trades a dev-group row for a hand-rolled parser that would have to model YAML
block structure to find job boundaries, and would be wrong in exactly the cases worth
catching.

### Decision 7 — Timeouts are per job, and sized by tier rather than uniformly

Every job carries `timeout-minutes`: 10 for `django.yml`'s lint job, 45 for its test matrix,
45 for the Postgres shards, 15 for the audit, and 15 / 25 for `kanban-pages.yml`'s `build` /
`deploy`.

A timeout's job is to convert a hang into a failure. Its value therefore has to sit far
enough above the observed run time that a slow-but-healthy run is not killed, and far
enough below GitHub's six-hour default that a wedged runner is released promptly. Uniform
values fail on one side or the other: 10 minutes on the test matrix would kill legitimate
full-matrix runs, and 45 on the lint job would hold a runner long past the point a static
check could still be working. The lint job runs static checks only; the test and Postgres
tiers install a Python, sync dependencies, and run the suite under `xdist`. The Pages
`deploy` job's value must exceed the deploy step's own polling timeout, so a slow Pages
backend is reported by the action instead of the job being killed mid-poll.

The values are deliberately generous rather than tight. A timeout tuned close to the current
run time becomes a flaky failure the first time a runner is slow, and a flaky gate gets
disabled — so the failure mode of a too-generous timeout (a wedged job held somewhat
longer) is strictly better than that of a too-tight one.

Reusable-workflow calls (`jobs.<id>.uses`) cannot carry `timeout-minutes`; the governance
test skips them for that reason rather than asserting something the platform forbids.

### Decision 8 — The governance posture is asserted by a test, not by review

`tests/test_ci_governance.py` parses every `*.yml` / `*.yaml` file in `.github/workflows/`
plus `.github/dependabot.yml` and asserts: each workflow is a YAML mapping with at least one
job; each declares exactly `permissions: {contents: read}` at the top level; no job grants
`contents: write`; every non-reusable job has a positive `timeout-minutes` and a `runs-on`;
every external `uses:` is pinned to a full 40-character SHA and carries a version comment;
every `actions/checkout` sets `persist-credentials: false`; at least one container image
reference exists and every one is digest-pinned; Dependabot covers both ecosystems; and the
audit workflow keeps both its `pull_request` and `schedule` triggers. The same module hosts
repo-tooling rows owned by other specs (the forbidden `DjangoOptimizerExtension` form sweep
and the install-floor constant pins); this card owns the workflow and Dependabot rows.

The Slice 2 posture is otherwise **structurally invisible to this repository**. Nothing
imports a workflow file, so a permission scope widening, a pin decaying to a tag, or a new
job landing with no timeout would each pass a fully green suite. The local remedy for a
governance rule with no runtime reachability is a repo-tool test — `tests/test_clean_up.py`
is the precedent — and this is the same shape.

The value it protects is the *next* change. The workflow edit made by someone who does not
know why `persist-credentials: false` is there is what the test is for, and every assertion
carries the reason in its docstring for that reader.

It is placed in root `tests/` under the
[Live-first coverage mandate][glossary-live-first-coverage-mandate]'s
genuinely-unreachable-live clause: a workflow YAML file cannot be reached from a fakeshop
`/graphql/` request by any route. It adds **no coverage exposure** — coverage's source is
`django_strawberry_framework` only, and the workflow rows import none of it, so
`fail_under = 100` is unaffected.

**Alternatives rejected.** A pre-commit hook — runs only for people who installed it, and
this must hold for a web-UI edit. `actionlint` — a good complement that checks workflow
*syntax and expressions*, but it does not encode this project's permission and pin
policies, which are the thing at risk. OpenSSF Scorecard in CI — reports a score rather
than failing a build, and needs its own token scope.

### Decision 9 — Workflow comments point at decisions

The workflow comments this card owns carry a `spec-049 Decision N` pointer rather than prose
restating the rationale, matching the `spec-044 Decision 6` reference in `django.yml`'s
matrix comment. A workflow file is the wrong place to relitigate a decision and the right
place to name it.

### Decision 10 — The version bump belongs to the joint cut

This card moves no version state. The release is single-sourced in
`django_strawberry_framework/__init__.py` `__version__`, which hatchling reads, and under the
[Joint version cut][glossary-joint-version-cut] rule the bump and the release wording belong
to the cut, never to one card's slices. Lock refreshes are dependency entries, not version
state, so they land on their own.

## Implementation plan

| Slice | Files | Carries |
|---|---|---|
| 1 | `uv.lock` | The audited resolution: Django behind the `python_full_version < '3.12'` / `>= '3.12'` split, every package off known advisories outside `osv-scanner.toml`'s expiring exemptions. |
| 2 | `.github/workflows/django.yml` | Top-level `permissions: contents: read`; `timeout-minutes` 10 / 45; both checkouts SHA-pinned with `persist-credentials: false`; `compatibility_only` on the exact-floor rows plus the job-name suffix and the contract comment. |
| 2 | `.github/workflows/postgres.yml` | Top-level `permissions: contents: read`; `timeout-minutes: 45`; checkout SHA-pinned with `persist-credentials: false`; `postgres@sha256:…` with the refresh-procedure comment. |
| 2 | `.github/workflows/kanban-pages.yml` | `checkout`, `configure-pages`, `upload-pages-artifact`, `deploy-pages` SHA-pinned with version comments; `persist-credentials: false` on the checkout; the `deploy` job's job-level `id-token` / `pages` grant. |
| 3 | `.github/workflows/dependency-audit.yml` | `pull_request` (paths-filtered) + daily `schedule` + `workflow_dispatch`; `permissions: contents: read`; `concurrency` group; `timeout-minutes: 15`; SHA-pinned checkout and `osv-scanner-action` with `--lockfile=uv.lock`. |
| 3 | `osv-scanner.toml` | Expiring, reasoned `[[IgnoredVulns]]` entries only. |
| 3 | `.github/dependabot.yml` | `uv` and `github-actions` ecosystems, weekly, `open-pull-requests-limit: 5`, commit-message prefixes, and the `dev-tooling` group. |
| 4 | `tests/test_ci_governance.py` | The workflow and Dependabot assertions in [Decision 8](#decision-8--the-governance-posture-is-asserted-by-a-test-not-by-review), parametrized per workflow file. |
| 4 | `pyproject.toml` | The `pyyaml>=6.0.2` dev-group row and its rationale comment. |
| 5 | `docs/GLOSSARY.md` (DB), `docs/README.md`, `SECURITY.md`, `docs/TREE.md`, `KANBAN.md` (DB) | Fold-in and the secure-version statement. |

## Helper-reuse obligations (DRY)

- **One audit tool and one scan target.** `osv-scanner` against `uv.lock` is the only
  vulnerability audit in the repository, and `osv-scanner.toml` its only exemption file. A
  second tool, or a second invocation over an exported requirements file, would produce two
  findings lists that disagree and two places to suppress.
- **One place per action pin.** Each action appears with its SHA and version comment at its
  `uses:` site and nowhere else; no `env` indirection, no repeated SHA constant. Dependabot
  rewrites `uses:` lines, so a pin held anywhere else silently stops being updated.
- **One governance module** owns every workflow assertion. A per-workflow test file would
  duplicate the loader and drift; the module parametrizes over the glob instead, so a new
  workflow file is covered the moment it lands.
- **One loader helper** (`_load`) and one job/step accessor pair (`_jobs`, `_steps`) inside
  that module. No assertion re-opens a file or re-implements the `None`-tolerant traversal
  that YAML's empty-mapping cases require.
- **One immutability rule, expressed once** as the `FULL_SHA` pattern. Both the SHA
  assertion and the version-comment assertion consult it rather than each spelling out
  "40 hex characters".

## Edge cases and constraints

- **A job-level `permissions` block replaces, not merges.** `kanban-pages.yml`'s `deploy`
  job therefore restates `contents: read` alongside its `id-token: write` / `pages: write`.
  Dropping the restatement to "inherit" the default would revoke read access, not add to it.
- **A reusable-workflow call cannot carry `timeout-minutes` or `runs-on`.** The governance
  test skips jobs with a `uses:` key rather than asserting platform-forbidden fields. No job
  here is such a call; the branch keeps adding one from presenting as a governance
  regression.
- **`yaml.safe_load` parses the `on:` key as the boolean `True`** under YAML 1.1's
  truthiness rules. The audit-trigger assertion reads `workflow[True]` with a `workflow["on"]`
  fallback rather than assuming either spelling.
- **Comments are stripped before matching image references.** The Postgres comment block
  names the `postgres:16` tag in prose while the `docker run` line is digest-pinned; matching
  raw text would flag the explanation as the violation.
- **A workflow directory with no files, or workflows with no image reference,** would make
  the parametrized assertions vacuously true. `_workflow_paths` asserts non-empty at import,
  and `test_workflow_container_images_are_present` asserts at least one image reference.
- **`persist-credentials: false` is safe only because nothing pushes.** A job that needs to
  push sets `persist-credentials: true` on its own checkout and amends the governance test
  in the same change — the assertion is the place that conversation is forced to happen.
- **The digest pin does not float across Postgres minor versions.** `postgres@sha256:…` is
  one image, so a `16.x` upstream patch requires a deliberate digest refresh, resolved from
  the registry manifest API. That is the intent.
- **The audit's `pull_request` paths filter means most PRs never run it.** A PR that cannot
  change the resolution or the exemptions has nothing to audit; the daily schedule covers the
  resolution itself.
- **The audit fails closed on a new advisory.** A non-zero scanner exit fails the job by
  design. There is no `continue-on-error`, because a supply-chain finding that does not
  block is a notification, and notifications nobody receives are how a stale lock goes
  unnoticed. An exemption reaching its `ignoreUntil` date fails the audit the same way.

## Test plan

| Tier | Row | Asserts |
|---|---|---|
| `tests/` | `test_workflow_parses` (per workflow) | Every workflow is a YAML mapping declaring at least one job. |
| `tests/` | `test_workflow_declares_top_level_read_only_permissions` (per workflow) | Top-level `permissions` is exactly `{contents: read}`. |
| `tests/` | `test_no_job_grants_repository_write` (per workflow) | No job's `permissions.contents` is `write`. |
| `tests/` | `test_every_job_declares_a_timeout` (per workflow) | Every non-reusable job has a positive integer `timeout-minutes`. |
| `tests/` | `test_every_job_declares_a_runner` (per workflow) | Every non-reusable job declares `runs-on`. |
| `tests/` | `test_every_external_action_is_pinned_to_a_full_commit_sha` (per workflow) | Every non-local `uses:` ref matches 40 hex characters. |
| `tests/` | `test_pinned_actions_keep_a_readable_version_comment` (per workflow) | Every SHA-pinned `uses:` line carries a `#` comment. |
| `tests/` | `test_checkout_steps_do_not_persist_credentials` (per workflow) | Every `actions/checkout` step sets `persist-credentials: false`. |
| `tests/` | `test_workflow_container_images_are_present` | At least one image reference exists in executable workflow text. |
| `tests/` | `test_container_images_are_pinned_by_digest` (per workflow) | Every image reference in executable (comment-stripped) workflow text uses `@sha256:`. |
| `tests/` | `test_dependabot_covers_python_and_github_actions` | `dependabot.yml` covers both the `uv` and `github-actions` ecosystems. |
| `tests/` | `test_dependency_audit_workflow_runs_on_pull_request_and_a_schedule` | Both triggers are present. |
| Command | `uv lock --check` | The lock is a valid resolution of the declared floors. |
| Command | `osv-scanner --lockfile=uv.lock` | Exits 0 against the lock, with `osv-scanner.toml`'s unexpired exemptions applied. |
| Command | `uv run pytest` | The full suite passes at `fail_under = 100` against the locked resolution. |

**What cannot be proven locally.** "CI green" is a statement about GitHub's runners. The
local substitutes are the three commands above plus the structural parse of every workflow;
the scheduled trigger, the Dependabot ecosystem resolution, and the runner-side behaviour of
each pinned action SHA are observable only on GitHub.

## Doc updates

Slice 5, all of it fold-in rather than new surface:

- `docs/README.md` — the secure-version statement, written against the `Django>=5.2.16`
  floor, in the [Production security profile][docs-readme-production-profile], the section a
  deployment review walks.
- [`SECURITY.md`][security] — the condensed statement beside its supported-versions table,
  including the `[compatibility floor]` label's meaning.
- `docs/GLOSSARY.md` (DB-rendered) — the secure-version statement in the
  [Hard dependency][glossary-hard-dependency] entry, whose subject is exactly the
  unconditionally-installed packages this concerns. No new term.
- `docs/TREE.md` (script-rendered) — the `tests/test_ci_governance.py` row.
- `KANBAN.md` (DB-rendered) — the card and its `SpecDoc`.

`docs/GLOSSARY.md`, `docs/TREE.md`, and `KANBAN.md` are generated. Their edits are made in
the source (the fakeshop glossary / kanban DB, or the module docstrings) and re-rendered,
never by hand.

## Risks and open questions

- **Dependabot's `uv` lockfile handling has open upstream issues.** Reports exist of update
  PRs that move `pyproject.toml` without regenerating `uv.lock`, or the reverse. The answer:
  ship the `uv` ecosystem anyway, because the audit in
  [Decision 5](#decision-5--osv-scanner-against-uvlock-on-a-clock-and-on-every-resolution-diff)
  reads `uv.lock` directly and would fail on a PR that left it stale — the two mechanisms
  check each other. Fallback if the PRs prove unusable: keep the `github-actions` ecosystem,
  drop the `uv` one, and add a scheduled `uv lock --upgrade-package` job per
  [Decision 6](#decision-6--dependabot-over-a-scheduled-uv-lock---upgrade-job)'s rejected
  alternative.
- **`osv-scanner`'s inner image tag is mutable**, per
  [Decision 4](#decision-4--immutable-pins-plus-the-mechanism-that-keeps-them-from-going-stale).
  The answer: accept and record, since the action definition is pinned. Fallback if a
  supply-chain incident touches that image: pin `ghcr.io/google/osv-scanner-action` by
  digest via a fork, accepting the maintenance cost then rather than now.
- **An advisory with no fixed release for a supported marker.** The correct response depends
  on whether the affected package is a [hard dependency][glossary-hard-dependency], a
  [soft dependency][glossary-soft-dependency], or dev-only; the mechanism is an
  `osv-scanner.toml` entry with a `reason` and a mandatory `ignoreUntil` date, never an
  open-ended suppression.
- **`pyyaml` is a dev-group dependency for a governance test.** Accepted, per
  [Decision 6](#decision-6--dependabot-over-a-scheduled-uv-lock---upgrade-job) — a hand-rolled YAML
  parser would be wrong precisely where the assertions matter.
- **A repository-level default token scope would strengthen
  [Decision 3](#decision-3--least-privilege-is-a-default-plus-a-visible-exception-not-a-per-job-audit)**
  but is a settings change, not a file. The maintainer sets the default workflow permissions
  to read-only in repository settings; the in-repo blocks make that change a no-op rather
  than a behaviour change, so the order is safe either way.
- **Timeout values are estimates, not measurements** — sized generously per
  [Decision 7](#decision-7--timeouts-are-per-job-and-sized-by-tier-rather-than-uniformly).
  Tighten against observed p95 once the matrix has history, never below 2x observed.

## Out of scope (explicitly tracked elsewhere)

- Secure output and error defaults — [`spec-048`][spec-048].
- The execution resource policy — [`spec-047`][spec-047].
- Transport security — [`spec-046`][spec-046].
- Extracting the debug extension into its own distribution —
  [`TODO-ALPHA-052-0.0.15`][kanban], which removes `extensions/debug.py` and changes the
  dependency surface the audit reads.
- Artifact signing, provenance attestation, and SLSA build levels — not carded. A publish
  workflow is the natural home and none exists.
- A self-hosted package mirror or private registry posture — not carded.
- OpenSSF Scorecard reporting in CI — rejected in
  [Decision 8](#decision-8--the-governance-posture-is-asserted-by-a-test-not-by-review);
  not carded.

## Definition of done

- [ ] `uv.lock` resolves Django behind the `python_full_version < '3.12'` / `>= '3.12'`
      split at the top of the audited range; `uv lock --check` passes; `pyproject.toml`
      declares `Django>=5.2.16`, and no supported configuration resolves Django below it.
- [ ] `osv-scanner --lockfile=uv.lock` exits 0, and the only suppression file is
      `osv-scanner.toml`, whose every entry carries a `reason` and an `ignoreUntil` date.
- [ ] Every workflow declares `permissions: contents: read` at the top level; no job grants
      `contents: write`; the only job-level elevation in the repository is
      `kanban-pages.yml`'s `deploy` (`id-token: write` / `pages: write`).
- [ ] Every `uses:` reference is a full 40-character commit SHA carrying a readable
      `# vX.Y.Z` comment, resolved from upstream rather than constructed; the Postgres image
      is pinned by `@sha256:` digest.
- [ ] Every `actions/checkout` sets `persist-credentials: false`; every job declares a
      positive `timeout-minutes`.
- [ ] The exact-floor matrix cell runs `Django==5.2.16` with `strawberry-graphql` at its
      declared floor, carries the `[compatibility floor]` job-name label and contract
      comment, and is not an input to the audit.
- [ ] `.github/workflows/dependency-audit.yml` runs on `pull_request`, on a `schedule`, and
      on `workflow_dispatch`, at `contents: read`, with no SARIF upload and no
      `security-events` scope.
- [ ] `.github/dependabot.yml` covers the `uv` and `github-actions` ecosystems.
- [ ] `tests/test_ci_governance.py` asserts the whole posture and adds no package coverage
      surface.
- [ ] No file under `django_strawberry_framework/` belongs to this card.
- [ ] Full suite green at `fail_under = 100` for `django_strawberry_framework`; `ruff
      format --check`, `ruff check`, and `scripts/check_trailing_commas.py --check` all
      clean.
- [ ] The secure-version statement is folded into `docs/README.md`, `SECURITY.md`, and the
      glossary.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../KANBAN.md
[security]: ../../SECURITY.md

<!-- docs/ -->
[docs-readme-production-profile]: ../README.md#production-security-profile
[glossary]: ../GLOSSARY.md
[glossary-hard-dependency]: ../GLOSSARY.md#hard-dependency
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: ../GLOSSARY.md#live-first-coverage-mandate
[glossary-per-operation-extension-isolation]: ../GLOSSARY.md#per-operation-extension-isolation
[glossary-require_optional_module]: ../GLOSSARY.md#require_optional_module
[glossary-soft-dependency]: ../GLOSSARY.md#soft-dependency

<!-- docs/SPECS/ -->
[spec-046]: spec-046-transport_security-0_0_14.md
[spec-047]: spec-047-resource_policy-0_0_14.md
[spec-048]: spec-048-secure_output_defaults-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
