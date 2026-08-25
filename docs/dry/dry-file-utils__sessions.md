# DRY review: `django_strawberry_framework/utils/sessions.py`

Status: verified

## System trace

`django_strawberry_framework/utils/sessions.py` implements the centralized session-store class resolver and connection actor lease synchronization primitive ([spec-040][spec-040], [spec-041][spec-041], [spec-046][spec-046]).

It owns the following architectural responsibilities:

1. **Session Engine Resolution:**
   - Session store resolver: [`session_store_class`][utils-sessions] (`django_strawberry_framework/utils/sessions.py::session_store_class`).

2. **Connection Actor State & Synchronization Lease:**
   - Private scope key: [`_ACTOR_STATE_SCOPE_KEY`][utils-sessions].
   - Connection actor record: [`ConnectionActorState`][utils-sessions] (`django_strawberry_framework/utils/sessions.py::ConnectionActorState` with `django_strawberry_framework/utils/sessions.py::ConnectionActorState.authenticated_provenance`, `django_strawberry_framework/utils/sessions.py::ConnectionActorState.lock`, `django_strawberry_framework/utils/sessions.py::ConnectionActorState.__init__`).
   - State accessors & latches: [`connection_actor_state`][utils-sessions] (`django_strawberry_framework/utils/sessions.py::connection_actor_state`), [`note_authenticated_actor`][utils-sessions] (`django_strawberry_framework/utils/sessions.py::note_authenticated_actor`), and [`connection_was_authenticated`][utils-sessions] (`django_strawberry_framework/utils/sessions.py::connection_was_authenticated`).
   - Lease management: [`actor_lease`][utils-sessions] (`django_strawberry_framework/utils/sessions.py::actor_lease`) and [`actor_transition`][utils-sessions] (`django_strawberry_framework/utils/sessions.py::actor_transition`).

Connected behavior examined:
- [`django_strawberry_framework/auth/sessions.py`][auth-sessions]: Session capability detection (`uses_signed_cookie_sessions`) and session locking.
- [`django_strawberry_framework/consumers.py`][consumers]: WebSocket per-operation actor revalidation and protected frame transmission.
- [`django_strawberry_framework/auth/mutations.py`][auth-mutations]: Channels logout teardown within `actor_transition`.
- [`tests/utils/`][tests-utils]: Test suite validating session engine resolution and connection actor lease concurrency.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/sessions.py --include-constants`):
- Parsed 1 target file, 252 lines.
- Complete inventory across all 11 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/sessions.py` provides the single shared synchronization point between the transport layer (`consumers.py`) and the auth layer (`auth/sessions.py`, `auth/mutations.py`):
   - `session_store_class` unifies session store instantiation without forcing opt-in auth dependencies onto raw WebSocket transport consumers.
   - `actor_lease` and `actor_transition` establish mutual exclusion between in-flight protected frame transmission and native actor teardown (`channels.auth.logout`).
   - `ConnectionActorState.authenticated_provenance` latches authenticated provenance to prevent logged-out sockets from claiming anonymous revalidation carve-outs.

2. **Sync and async twins:**
   Actor state operations and leases are asynchronous (`asyncio.Lock`), matching Channels ASGI connection lifecycles.

3. **Derived rather than repeated knowledge:**
   `connection_actor_state` creates `ConnectionActorState` lazily on first access in an `await`-free, atomic step.

4. **Inverse and round-trip pairs:**
   `actor_lease` (held across validate/send sequences) and `actor_transition` (held across actor teardown) form the symmetric reader-writer mutual exclusion pair.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/sessions.py`][utils-sessions], [`django_strawberry_framework/consumers.py`][consumers], [`django_strawberry_framework/auth/sessions.py`][auth-sessions], [`django_strawberry_framework/auth/mutations.py`][auth-mutations];
   - Specifications: [`docs/SPECS/spec-040-bulk_mutations-0_0_12.md`][spec-040], [`docs/SPECS/spec-041-channels_subscriptions-0_0_13.md`][spec-041], [`docs/SPECS/spec-046-composite_pk_support-0_0_14.md`][spec-046];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/auth/`][tests-auth];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Altering the session store class lookup or settings resolution):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/sessions.py`][utils-sessions] ([`session_store_class`][utils-sessions]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying the connection actor state slot layout or provenance latching):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/sessions.py`][utils-sessions] ([`ConnectionActorState`][utils-sessions] / [`note_authenticated_actor`][utils-sessions]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Changing the actor lease acquisition protocol or transition context manager):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/sessions.py`][utils-sessions] ([`actor_lease`][utils-sessions] / [`actor_transition`][utils-sessions]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Placing session store resolution in `auth/sessions.py`:**
   - Disproved per [spec-040][spec-040]. `auth/__init__.py` eagerly loads GraphQL mutation and type registries; importing from `auth` in transport code breaks the opt-in architecture.

## Opportunities

None — `django_strawberry_framework/utils/sessions.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/sessions.py` exhibits zero duplicate code and complete policy consolidation across session store resolution and connection actor synchronization. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/sessions.py --review docs/dry/dry-file-utils__sessions.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/sessions.py`][utils-sessions] and Worker 1's DRY review.

1. **Session Engine & Actor Synchronization:**
   - Confirmed `session_store_class` dynamically resolves the engine at call time via Django's `import_string`.
   - Confirmed `actor_lease` and `actor_transition` strictly serialize frame transmission against actor transitions.
   - Confirmed `note_authenticated_actor` latches authentication state irrevocably for the socket duration.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/sessions.py --review docs/dry/dry-file-utils__sessions.md --include-constants`. 100% coverage across all 11 definitions / constants.

Confirmed: `django_strawberry_framework/utils/sessions.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-040]: ../SPECS/spec-040-bulk_mutations-0_0_12.md
[spec-041]: ../SPECS/spec-041-channels_subscriptions-0_0_13.md
[spec-046]: ../SPECS/spec-046-composite_pk_support-0_0_14.md

<!-- package source -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-sessions]: ../../django_strawberry_framework/auth/sessions.py
[consumers]: ../../django_strawberry_framework/consumers.py
[utils-sessions]: ../../django_strawberry_framework/utils/sessions.py

<!-- tests -->
[tests-auth]: ../../tests/auth/
[tests-utils]: ../../tests/utils/
