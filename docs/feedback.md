# Spec Review (Round 2): Auth Mutations spec-040-auth_mutations-0_0_13

Rigorous review of `docs/spec-040-auth_mutations-0_0_13.md` (Revision 5) ahead of the `0.0.13` implementation.

---

## 1. Verification of Prior Findings & Revision 5 Integration

The Revision 5 changes perfectly capture and single-site resolve the critical gaps identified in the first review:
- **P1 Error Keying resolved**: The spec now dictates that the register `write_step` intercepts list-style `ValidationError`s from `validate_password` at the call-site and maps them directly to `password`-keyed `FieldError`s, avoiding the non-dict `"__all__"` fallback.
- **P1 Plaintext Password Leak resolved**: The explicit `decode_step` tuple signature extraction `(user, m2m_assignments, exclude, raw_password)` ensures that the raw password never touches the constructed model attributes in memory prior to hashing.
- **P2 Lifecycle & Clear Split resolved**: Correct separation between `TypeRegistry.clear()` for declarations and `register_subsystem_clear` for emit artifacts is fully pinned.

---

## 2. Round 2 Deep-Dive Implementation Findings

### P2: Resolving and Typing `current_user()` using Dispatcher Signature Injection
- **The Finding**: At class-body time (when the `current_user()` field factory is evaluated), the consumer's primary type (e.g., `UserType`) is not yet resolved. Therefore, the resolver signature cannot be statically annotated with the actual class.
- **The Avoidance**: To match the package's existing field factory design pattern established in `DjangoMutationField` (`mutations/fields.py`), the `current_user()` field factory must dynamically attach `__signature__` and `__annotations__` to its dispatcher resolver.
- **The Concrete Type Signature**:
  The return annotation on the dispatcher resolver must be:
  `Optional[Annotated["CurrentUserAlias", strawberry.lazy("django_strawberry_framework.auth.queries")]]`
  During `bind_auth_mutations()` finalization, the queries module must dynamically set `CurrentUserAlias = primary_type`. This ensures Strawberry resolves the lazy reference correctly at schema compile time.

### P2: Strict Thread-Safety & Lazy User Evaluation under `sync_to_async`
- **The Finding**: In an async context, `request.user` is loaded lazily via a `SimpleLazyObject` wrapper. Accessing any attribute on `request.user` (including `is_authenticated`) triggers synchronous ORM queries, which raises a `SynchronousOnlyOperation` exception if done outside `sync_to_async`.
- **The Avoidance**: Both the authentication check and the write-permission carrier validation must run inside the synchronous closure wrapped by `sync_to_async(thread_sensitive=True)`.
- **Sync/Async Dispatcher Structure**:
  - **Sync**:
    - Extract user off request.
    - Run permission gate checks via `authorize_or_raise`.
    - Return user if authenticated, else `None`.
  - **Async**:
    - Wrap the entire permission check and user evaluation block inside a sync helper.
    - Run the sync helper using `await sync_to_async(helper, thread_sensitive=True)()`.

### P3: Session Token Rotation and Token Validation
- **The Finding**: In `login`'s resolver, `auth.login(request, user)` handles the session key cycling (the fixation defense). However, standard Django login rotates only the CSRF token on `rotate_token(request)`.
- **The Avoidance**: Rely entirely on Django's native `auth.login` and `auth.logout` for session manipulation inside the `sync_to_async` boundary, avoiding any bespoke session key management that could diverge from the configured session backend.

---

## 3. Finalized Implementation Checklist

- [ ] **Manual Password Error Keying**: Verify that `Register`'s `write_step` manually maps the `validate_password` `ValidationError` to `"password"`.
- [ ] **Extended Decode Tuple**: Assert in the unit tests that `user` never carries a plaintext `password` attribute during or after the `decode_step`.
- [ ] **Queries Alias Namespace**: Register `CurrentUserAlias` on `register_subsystem_clear` and ensure `queries.CurrentUserAlias` is set to the primary type inside `bind_auth_mutations()`.
- [ ] **Type Signature Injection**: Attach `__signature__` and `__annotations__` to the `current_user` resolver dispatcher, matching `DjangoMutationField`'s injection pattern.
- [ ] **Enclosed Async Lazy Loading**: Ensure all lazy evaluations (MRO, querysets, or user properties) are completely contained within the `sync_to_async` boundary on the async path.
- [ ] **AGENTS.md Compliance**: Prepend `create_users(N)` as the first line of every live and internal auth test case.