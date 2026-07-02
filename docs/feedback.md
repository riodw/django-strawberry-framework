# Spec Review: Auth Mutations spec-040-auth_mutations-0_0_13

Rigorous review of `docs/spec-040-auth_mutations-0_0_13.md` ahead of the `0.0.13` implementation.

---

## 1. Critical Security & Correctness Gaps (P1)

### Plaintext Password Leak in `register_mutation`
- **The Risk**: If the raw password remains in the input attributes when constructing the user model, `model(**scalar_and_fk_attrs)` would instantiate the user with a plaintext password attribute (e.g., `user.password = raw_password`). This is a severe security hazard: other model hooks, signals, serialization libraries, or debug loggers could capture or output this plaintext string before `set_password` runs.
- **The Avoidance**: The `decode_step` of the synthesized `Register` rider must explicitly pop `"password"` from the input dictionary *before* constructing the model instance or assigning attributes. The raw password must travel *only* within the extended tuple `(user, m2m_assignments, exclude, raw_password)` to the `write_step`.
- **Validation**: Enforce a unit assertion in `tests/auth/test_mutations.py` verifying that the constructed user model instance never receives `"password"` in its attributes during the decode step.

### Mis-keying of Password Validator Failures
- **The Risk**: Django's password validators raise a list-style `ValidationError`. If the `ValidationError` is passed to the generic `validation_error_to_field_errors(exc)` utility, it will map it to `NON_FIELD_ERRORS` (`"__all__"`), because there is no field dictionary.
- **The Avoidance**: In `Register`'s `write_step`, wrap the `validate_password` block and manually map the `ValidationError` to a `"password"`-keyed `FieldError`:
  ```python
  try:
      validate_password(raw_password, user)
  except ValidationError as e:
      return [field_error("password", list(e.messages), codes=[leaf.code for leaf in e.error_list if leaf.code])]
  ```

---

## 2. Architectural & Design Consistencies (P2)

### `current_user` Return Type Alias
- **The Risk**: At class-body evaluation time (when `current_user()` is called), the consumer's primary `UserType` is not yet finalized or resolved. Thus, `current_user` must type its field return as `Optional[CurrentUserAlias]` via a lazy forward-reference.
- **The Avoidance**:
  - The `queries.py` module must register `CurrentUserAlias` as its emit ledger under `register_subsystem_clear`.
  - During `bind_auth_mutations()`, resolve the user's primary type and bind it:
    ```python
    setattr(queries_module, "CurrentUserAlias", primary_type)
    ```
  - This ensures Strawberry successfully maps the alias to the concrete user type at schema compile time, generating `me: UserType` in the SDL.

### Duck-Typed Permission Holders Constraint
- **The Risk**: Because `login`, `logout`, and `current_user` are model-less fields rather than real subclasses of `DjangoMutation`, they use a custom duck-typed holder class to pass to `authorize_or_raise`.
- **The Avoidance**: Custom `has_permission` hooks that inspect the `mutation` positional argument (e.g. reading `mutation.Meta.model` or checking inheritance) will raise an `AttributeError` or type mismatch at request time.
- **The Remedy**: Document this limitation clearly: permission gates on the three model-less fields must only key on `info`, `operation`, or `data`, never on the `mutation` class itself. Add a test asserting that a gate introspecting `mutation` fails cleanly with a request-time exception, validating the `DenyAll` precedent.

---

## 3. Implementation Detail & Edge Cases (P3)

### Multi-Pass Finalization and Ledger Isolation
- **The Risk**: If the auth declaration ledger is added to `register_subsystem_clear`, it will be drained during the finalizer's pre-bind reset loop, before `bind_auth_mutations()` is ever invoked.
- **The Avoidance**:
  - Keep the **declaration** ledger (containing class-body registrations) on the `TypeRegistry.clear()` hand row alongside `clear_mutation_registry`. This ensures registrations survive re-finalize passes.
  - Keep the **emit** ledgers (such as `LoginPayload`, `LogoutPayload` in `mutations.inputs` and `queries.CurrentUserAlias`) on the pre-bind reset loop (`register_subsystem_clear`), allowing them to be cleanly rebuilt.

### Async Context Security & Lazy User Forcing
- **The Risk**: Accessing `request.user` lazily in an async resolver can raise `SynchronousOnlyOperation` if it hasn't been fetched from the database yet.
- **The Avoidance**: Within the async resolver for `current_user` or the permission checks, ensure that `request.user.is_authenticated` (or any attribute access) is fully evaluated inside the `sync_to_async(thread_sensitive=True)` worker block.

### Test Seeding Rule Compliance
- **The Risk**: Violating the catalog/auth test seeding rules in `AGENTS.md`.
- **The Avoidance**: Ensure every test in `examples/fakeshop/test_query/test_auth_api.py` begins with `create_users(N)` from `apps.products.services`. Do not hand-roll `User` objects or seed data outside the approved helper.

---

## 4. Concrete Bug-Avoidance Checklist

- [ ] **Decode Pop**: Ensure `Register`'s `decode_step` pops `"password"` off before creating the model instance.
- [ ] **Field-Keyed Password Errors**: Specifically catch `ValidationError` around `validate_password` and key to `"password"`.
- [ ] **Pre-Bind Ordering**: Wire `bind_auth_mutations()` *before* `bind_mutations()` to prevent the generic `_resolve_primary_type` error from pre-empting the register-specific missing-type error.
- [ ] **Alias Reset**: Add `current_user`'s alias namespace to `register_subsystem_clear` and the auth declaration ledger to `TypeRegistry.clear()`.
- [ ] **Async Thread-Safety**: Ensure all Django session, authentication, and lazy user loading are strictly enclosed within a single `sync_to_async(thread_sensitive=True)` context.
- [ ] **No DjangoModelPermission on Model-less fields**: Custom rate-limiters or IP-check permission classes must ignore the `mutation` parameter.