# DRY review: `django_strawberry_framework/keyset.py`

Status: verified

## System trace

`keyset.py` is the package-owned codec and seek vocabulary for `Meta.cursor_field`
("keyset"/value-encoded) Relay cursors: `CursorColumn` / `KeysetCursor` / `KeysetSeek` model one
resolved ordering column, one decoded cursor, and one fully-resolved seek; `split_order_ref` /
`validate_cursor_field_references` / `validate_cursor_field_columns` own the declaration-time and
finalization-time `cursor_field` syntax and column contract (local, concrete, non-nullable,
unique-terminal); `cursor_columns_for` resolves a validated reference tuple to model fields;
`encode_keyset_cursor` / `decode_keyset_cursor` are the ONE authenticated-encrypted (AES-SIV)
codec every strategy mints and decodes through; `keyset_seek_q` builds the ORM `Q` seek predicate
(redundant leading bound + OR-expansion); `order_fingerprint` derives the replay-guard fingerprint
embedded in every cursor.

Traced every caller and sibling implementation:

- `types/base.py::_validate_cursor_field` calls `validate_cursor_field_references` at
  class-creation time (shape/syntax only); `types/finalizer.py` calls
  `validate_cursor_field_columns` at finalization (column existence/concreteness/nullability/
  unique-terminal, needing the settled model field surface).
- `connection.py` is the primary consumer: `_keyset_connection_context` resolves and caches the
  declared-cursor_field state via `cursor_columns_for` + `order_fingerprint`; `_keyset_order_state`
  derives the ROOT per-`orderBy:` state (declared-order fast path, or a per-entry resolution that
  validates non-nullable/non-JSON/local-or-related columns using the SAME
  `_is_supported_cursor_field` predicate keyset.py exports); `_resolve_keyset_connection` is the
  framework-owned slicer that calls `decode_keyset_cursor` / `KeysetSeek(...).q()` /
  `encode_keyset_cursor` for every non-window keyset path (root and per-parent fallback);
  `_resolve_from_window` mints keyset edge cursors for the windowed fast path through the same
  `encode_keyset_cursor`.
- `optimizer/nested_planner.py::_keyset_cursor_context` resolves a relation target's keyset
  columns/fingerprint (the declared `cursor_field` only - v1 nested keyset windows do not support
  a per-relation `orderBy:` override); `_keyset_window_slice_from_arguments` decodes a nested
  `after:`/`before:` cursor through `decode_keyset_cursor` and builds a `KeysetSeek`.
- `optimizer/plans.py::apply_window_pagination` accepts a `keyset_seek: KeysetSeek | None` and
  calls `keyset_seek.q()` (never reimplements the predicate) to seed the base `WHERE` (count-free
  shape) or the count window's `Count(1, filter=seek_q)` (counted shape).
- `optimizer/lateral_fetch.py::build_lateral_sql` renders the SAME seek as raw Postgres SQL inside
  the lateral branch (uniform-direction row-value comparison, or the identical redundant-leading-
  bound OR-expansion for mixed ASC/DESC) so the two dialects return byte-identical row sets;
  `_keyset_seek_quals_match` structurally re-derives the planned seek's WHERE residue at fetch time
  to prove Django's prefetch machinery attached nothing else.
- `examples/fakeshop` (`apps/library/models.py::Book`/`Issue` declare `cursor_field`) and
  `examples/fakeshop/test_query/test_keyset_api.py` exercise the full contract live over HTTP
  (opacity, forward/backward round trips, insert stability, permission-aware decode, nested
  parity); `tests/test_keyset.py` and `tests/optimizer/test_lateral_fetch.py` pin the package-side
  codec, bounds, and dual-dialect seek rendering.

## Verification

- Compared `keyset.py::split_order_ref` against `optimizer/plans.py::order_entry_name_and_direction`
  (both parse one `order_by`-shaped entry into `(name, descending)`). The keyset.py docstring
  already names the distinction and reading both confirms it holds: `split_order_ref` is a
  CONFIGURATION-time syntax gate (raises `ConfigurationError` naming the offending entry, rejects
  `__`-relation traversal outright) called from `types/base.py`/`types/finalizer.py` where a
  malformed `Meta.cursor_field` entry must fail loudly; `order_entry_name_and_direction` is a
  BEST-EFFORT parser (`connection.py::_keyset_order_ref`, `optimizer/nested_planner.py`,
  `optimizer/lateral_fetch.py::_order_columns`) that returns `None` on anything it cannot resolve
  (an aggregate alias, a `nulls_first`/`nulls_last` expression, a relation path) so the caller can
  choose a fallback - a root `orderBy:` entry a value cursor cannot anchor is a `GraphQLError` at
  QUERY time, not a schema-build error, and a `__`-relation entry is explicitly SUPPORTED there
  (`connection.py::_resolve_order_path_field` walks it) where `cursor_field` itself forbids it.
  Rejected: same shape, opposite error-handling contract and a real behavioral difference
  (relation-path support) driven by two different callers' obligations.
- Compared `connection.py::_keyset_order_state`'s per-`orderBy:` resolution against
  `optimizer/nested_planner.py::_keyset_cursor_context`. Both ultimately call
  `cursor_columns_for` + `order_fingerprint`, but `_keyset_order_state` additionally derives columns
  from an ARBITRARY effective order (including `__`-relation entries via annotation) while
  `_keyset_cursor_context` only ever reads the DECLARED `cursor_field` (v1 nested keyset windows
  have no per-relation `orderBy:` override - confirmed by grep: no `orderBy:` argument threads into
  a nested keyset window anywhere in `optimizer/`). Rejected: the nested path is a strict subset of
  the root path's responsibility, not a second implementation of the same rule; both already
  delegate the resolution primitives themselves to `keyset.py`.
- Compared `keyset.py::keyset_seek_q`'s per-column direction rule
  (`greater = column.descending if flip else not column.descending`, duplicated inline for the loop
  arm and the leading-bound arm) against `optimizer/lateral_fetch.py::_keyset_seek_greater`
  (`return descending if flip else not descending`), used at two call sites
  (`_keyset_seek_sql`, `_keyset_seek_quals_match`) to render/verify the identical seek as raw SQL.
  The lateral_fetch.py docstring already named it "the lateral twin of the direction rule in
  `keyset.keyset_seek_q`" - an acknowledged duplicate, not an independent design. Confirmed by
  inputs/outputs: both are pure `f(descending: bool, flip: bool) -> bool` with byte-identical truth
  tables and the SAME reason to change (the keyset module docstring's cross-strategy byte-parity
  invariant explicitly claims this rule for "the windowed strategy, the lateral strategy, ... and
  root connections"). A silent edit to one arm (e.g. a future backend-specific tweak) would flip the
  seek direction for exactly one dialect and corrupt pagination without either test suite naming
  the other implementation. Accepted - see Opportunities.
- Searched `django_strawberry_framework/` for other `descending`/`flip`-shaped predicates,
  redundant-leading-bound constructions, and `_invalid_cursor_error`-shaped uniform-error patterns;
  found none outside the traced sites. `keyset_seek_q`'s OR-expansion shape and
  `lateral_fetch.py::_keyset_seek_sql`'s raw-SQL rendering remain intentionally separate
  (ORM `Q` tree vs. parameterized SQL text for a `CROSS JOIN LATERAL` subquery) - a prior review of
  `connection.py` already traced and rejected merging the two dialects' rendering wholesale; this
  review's finding is the single boolean formula underneath both renderers, not the renderers
  themselves.
- Ran the full focused suite after implementing: `tests/test_keyset.py`,
  `tests/optimizer/test_lateral_fetch.py` (119 passed), plus `tests/test_connection.py`,
  `tests/test_keyset_connection.py`, and `tests/optimizer/` (660 passed) - `--no-cov`.

## Opportunities

**Repeated responsibility.** The keyset seek DIRECTION rule - whether one ordering column's seek
comparison points "greater" given its own `descending` flag and the seek's `flip` (forward
`after:` vs. backward `before:`) - was defined identically in two places or the two enforcement
sites.

**Sites.**

- `django_strawberry_framework/keyset.py::keyset_seek_q` (two inline occurrences: the per-column
  loop arm and the leading-bound arm).
- `django_strawberry_framework/optimizer/lateral_fetch.py::_keyset_seek_greater`, consumed by
  `_keyset_seek_sql` (SQL rendering) and `_keyset_seek_quals_match` (fetch-time structural
  verification that the rendered seek is exactly what Django's prefetch WHERE carries).

**Evidence.** Byte-identical truth table (`descending if flip else not descending`), the same two
call reasons (mint a comparison operator for the ORM seek vs. render/verify the same comparison as
raw SQL), and the same invariant that must hold across both: `keyset.py`'s own module docstring
claims "the windowed strategy, the lateral strategy, ... and root connections all mint and decode
through THIS module, so a cursor minted by any path replays on every other" - the seek direction is
part of that cross-strategy contract, not an independent per-backend decision. The two
implementations had already been narrated as duplicates in `lateral_fetch.py`'s own docstring
("the lateral twin of the direction rule in `keyset.keyset_seek_q`") without ever being unified.

**Owner.** `django_strawberry_framework/keyset.py` - the module that already owns the ORM seek
predicate, the codec, and the fingerprint contract for every keyset strategy.

**Consolidation.** Added `keyset.py::keyset_seek_greater(descending: bool, *, flip: bool) -> bool`
as the single public direction rule. `keyset_seek_q` now calls it for both the loop arm and the
leading-bound arm. `optimizer/lateral_fetch.py` imports it directly, deletes its local
`_keyset_seek_greater`, and both former call sites (`_keyset_seek_sql`, `_keyset_seek_quals_match`)
now call the canonical function.

**Proof.** Added `tests/test_keyset.py::test_keyset_seek_greater_direction_table` (the four-entry
truth table over `descending x flip`) as a package-tier permanent test - `keyset_seek_greater` is a
package-owned pure predicate with no live-GraphQL surface of its own (it never appears as
resolvable behavior distinguishable from the seek results already covered live), so per AGENTS.md's
test-placement rule this is the strongest reachable tier. The existing behavioral coverage
(`tests/test_keyset.py::test_keyset_seek_q_mixed_directions_both_ways`,
`tests/optimizer/test_lateral_fetch.py::test_lateral_count_free_keyset_renders_in_branch_seek` /
`test_lateral_uniform_keyset_renders_row_value_seek` /
`test_lateral_single_column_keyset_renders_scalar_seek` /
`test_lateral_seek_quals_match_rejects_shape_drift`, and the live
`examples/fakeshop/test_query/test_keyset_api.py` forward/backward round trips) already exercises
every `(descending, flip)` combination through both call sites and passed unchanged after the
consolidation (119 focused + 660 broader tests, `--no-cov`).

**Risks / non-goals.** Does not touch the OR-expansion / redundant-leading-bound SHAPE, which stays
two intentionally separate renderers (a Django `Q` tree vs. parameterized raw SQL for a Postgres
`LATERAL` subquery) - unifying those would require one side to abandon its native representation
for no behavioral gain, and a prior `connection.py` DRY pass already traced and rejected that
broader merge. Does not touch `split_order_ref` vs. `order_entry_name_and_direction` (rejected
above) or the root-vs-nested `orderBy:` resolution split (rejected above).

## Judgment

One real, narrow consolidation: the pure seek-direction boolean was defined twice with an
already-acknowledged-but-never-fixed duplication comment; it now has one owner in `keyset.py` that
both the ORM and raw-SQL renderers call. Every other keyset/cursor/seek/order-policy candidate
traced from this file - the two order-string parsers, the root-vs-nested `orderBy:` resolution
split, and the ORM-vs-lateral-SQL seek rendering - encodes a genuinely different contract or
serves a genuinely different caller obligation and stays separate. Ready for Worker 2.

## Implementation (Worker 1)

Owner: `django_strawberry_framework/keyset.py` (new public `keyset_seek_greater`).

Migrated sites: `keyset.py::keyset_seek_q` (both direction-rule occurrences now call the new
function instead of inlining the formula); `optimizer/lateral_fetch.py` (removed the local
`_keyset_seek_greater`, imported `keyset_seek_greater` from `..keyset`, updated both call sites in
`_keyset_seek_sql` and `_keyset_seek_quals_match`).

Added test: `tests/test_keyset.py::test_keyset_seek_greater_direction_table` (package tier, per
AGENTS.md test-placement - this is a package-internal pure predicate with no independent live-query
surface beyond the seek behavior already covered end-to-end).

Behavior kept separate: the OR-expansion/redundant-leading-bound rendering shape stays two
backend-specific implementations (ORM `Q` vs. raw SQL); `split_order_ref` vs.
`order_entry_name_and_direction` and the root-vs-nested `orderBy:` split stay separate per the
rejected-candidate evidence above.

Validation: `uv run ruff format .` and `uv run ruff check --fix .` scoped to the three edited files
(clean, no changes beyond the edit itself). Focused tests:
`tests/test_keyset.py tests/optimizer/test_lateral_fetch.py` (119 passed, `--no-cov`); broader
`tests/test_connection.py tests/test_keyset_connection.py tests/optimizer` (660 passed, `--no-cov`).
Item-scoped diff (`git diff dd8b87d219f392d3f72c26d5f9a39ecb2fea6fa9 -- django_strawberry_framework/keyset.py
django_strawberry_framework/optimizer/lateral_fetch.py tests/test_keyset.py`) contains exactly the
changes described above; no unrelated concurrent-session file was touched.

Does not merit a changelog entry (internal refactor, no observable behavior change, no maintainer
authorization sought or needed for this scope).

## Independent verification (Worker 2)

Re-traced the target from scratch rather than reviewing only the edited lines: read the complete
`keyset.py` module docstring and every public function, then independently walked
`types/base.py::_validate_cursor_field`, `types/finalizer.py::validate_cursor_field_columns`,
`connection.py::_keyset_connection_context` / `_keyset_order_state` / `_resolve_keyset_connection`,
`optimizer/nested_planner.py::_keyset_cursor_context` / `_keyset_window_slice_from_arguments`,
`optimizer/plans.py::apply_window_pagination`, and `optimizer/lateral_fetch.py::build_lateral_sql` /
`_keyset_seek_sql` / `_keyset_seek_quals_match`.

**Diff scope.** `git diff dd8b87d219f392d3f72c26d5f9a39ecb2fea6fa9 -- django_strawberry_framework/keyset.py
django_strawberry_framework/optimizer/lateral_fetch.py tests/test_keyset.py` matches the artifact
exactly: one new public `keyset_seek_greater(descending, *, flip)` in `keyset.py`, both inline
occurrences in `keyset_seek_q` replaced with calls to it, `lateral_fetch.py`'s local
`_keyset_seek_greater` deleted with an import of the canonical function substituted at both of its
former call sites, and one new permanent test. Confirmed the baseline commit's own diff
(`git show dd8b87d219f392d3f72c26d5f9a39ecb2fea6fa9 --stat`) does not touch any of the three files, so
the item-scoped diff is entirely Worker 1's change with no baseline noise folded in.

**Migration completeness.** `rg` for `_keyset_seek_greater` and for the raw
`descending if flip else not descending` / `not descending if flip else descending` formula across
the whole package found exactly one definition of `keyset_seek_greater` (`keyset.py`) and zero
remaining inline occurrences of the formula anywhere, including `connection.py` (which never
reimplements the rule - `_keyset_order_state` and `_resolve_keyset_connection` route every seek
through `KeysetSeek.q()` -> `keyset_seek_q`, never a hand-rolled comparison). Both former
`lateral_fetch.py` call sites (`_keyset_seek_sql`, `_keyset_seek_quals_match`) now import and call
the canonical function; read both in full to confirm the substitution is a straight call-site swap
with no behavior drift.

**Rejected-candidate re-verification.**

- `split_order_ref` vs. `optimizer/plans.py::order_entry_name_and_direction`: read both bodies in
  full. Confirmed independently that `split_order_ref` raises `ConfigurationError` on anything it
  cannot parse and explicitly rejects `__`-relation traversal, while `order_entry_name_and_direction`
  returns `None` on the same inputs and is consumed by three fallback-tolerant callers
  (`connection.py`, `nested_planner.py`, `lateral_fetch.py::_order_columns`). A real, currently-live
  behavioral divergence, not just an error-handling label: `connection.py::_keyset_order_state` walks
  a `__`-relation `orderBy:` entry via `_resolve_order_path_field` (grepped and read the call site),
  which `cursor_field`'s syntax gate forbids outright. Two genuinely different caller obligations;
  rejection upheld.
- Root vs. nested `orderBy:` resolution split (`connection.py::_keyset_order_state` vs.
  `optimizer/nested_planner.py::_keyset_cursor_context`): read `_keyset_cursor_context` in full - it
  only ever reads the declared `cursor_field`, never an effective/per-relation order. Independently
  grepped `orderBy` across `django_strawberry_framework/optimizer/` and confirmed the only two hits
  are a `nested_planner.py` comment stating that a `filter:`/`orderBy:` sidecar on a relation field
  makes that key stay UNPLANNED (falls out of the keyset-window path entirely) and an unrelated
  `walker.py` comment about alias batching. No code path threads a per-relation `orderBy:` into a
  nested keyset window today, so `_keyset_cursor_context` is confirmed a strict subset of
  `_keyset_order_state`'s responsibility, not a second implementation of the same rule. Rejection
  upheld.
- ORM `Q` seek vs. lateral raw-SQL seek rendering (the renderer SHAPE, not the direction boolean):
  read `keyset_seek_q` and `_keyset_seek_sql` side by side. The OR-expansion/redundant-leading-bound
  logic is genuinely re-expressed per dialect (parameterized `Q` tree vs. literal SQL text assembled
  for a `CROSS JOIN LATERAL` subquery with positional `%s` placeholders) - collapsing them would force
  one side off its native representation for no behavioral gain. Correctly left separate; only the
  single boolean formula underneath both was the real duplicate.

**Equivalence proof.** Independently ran the full stated focused suite plus the broader net named in
the artifact: `tests/test_keyset.py tests/optimizer/test_lateral_fetch.py tests/test_connection.py
tests/test_keyset_connection.py tests/optimizer` (714 passed, `--no-cov`) - a superset of the 119 +
660 the artifact reports, since this run collected all of `tests/optimizer/` and both keyset-adjacent
connection suites together with no overlap deduction. Read
`test_keyset_seek_greater_direction_table` and confirmed its four assertions are the complete
`(descending, flip)` truth table with no gaps. Read `test_keyset_seek_q_mixed_directions_both_ways`
and the `tests/optimizer/test_lateral_fetch.py` seek-rendering tests and confirmed they exercise the
ORM and raw-SQL renderers through real mixed-direction data, so the consolidated function is proven
by behavior, not merely by the new unit test's truth table in isolation. Re-ran
`uv run ruff format --check` and `uv run ruff check` scoped to the three edited files: clean.

**Unrelated work check.** The three-file diff contains nothing beyond the direction-rule
consolidation - no incidental renames, no touched call sites outside the two seek renderers, no
absorbed concurrent work. The wider working tree carries substantial unrelated dirty state (other
files across the package, examples, and tests) matching the conversation's starting `git_status`;
none of it overlaps `keyset.py`, `optimizer/lateral_fetch.py`, or `tests/test_keyset.py`, so it is
out of scope for this item per `AGENTS.md`'s concurrent-work rule and was left untouched.

**Conclusion.** The claimed shared responsibility is real (one pure `f(descending, flip) -> bool`
formula, previously duplicated with an already-acknowledged-but-unfixed docstring cross-reference),
every consumer migrated, no leftover local implementation or parallel boolean remains anywhere in the
package, the rejected candidates hold up under independent re-tracing, and the new owner
(`keyset.py::keyset_seek_greater`) is clearer than the prior silent duplication. No further changes
needed.

Status: verified.
